"""LLM 字段抽取代理。"""

import json
import time
from dataclasses import dataclass

from openai import OpenAI

from app.agents.llm import create_structured
from app.config import get_settings
from app.prompt import load_messages

BASIC_FIELDS = [
    "合同标题",
    "合同编号",
    "签约主体",
    "对方名称",
    "金额",
    "币种",
    "生效时间",
    "到期时间",
]
CLAUSE_FIELDS = [
    "付款条款",
    "交付条款",
    "验收条款",
    "违约条款",
    "保密条款",
    "数据条款",
    "知识产权条款",
    "争议解决条款",
]
ALL_FIELDS = BASIC_FIELDS + CLAUSE_FIELDS

_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field_name": {"type": "string"},
                    "field_value": {"type": "string"},
                    "raw_text": {"type": "string"},
                    "page_no": {"type": "integer"},
                    "extract_status": {"type": "string", "enum": ["extracted", "missing"]},
                },
                "required": ["field_name", "field_value", "raw_text", "page_no", "extract_status"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["fields"],
    "additionalProperties": False,
}


@dataclass(slots=True)
class ParseField:
    """单个解析字段。"""

    field_name: str
    field_value: str
    raw_text: str
    page_no: int
    extract_status: str


@dataclass(slots=True)
class ContractParseResult:
    """解析结果。"""

    basic_info: dict
    clauses: dict
    fields: list[ParseField]
    parse_status: str
    parse_error: str | None = None


def _get_client() -> OpenAI:
    """按 .env 创建 OpenAI 兼容客户端，未配置时明确失败。"""
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_base_url.startswith(("http://", "https://")):
        raise RuntimeError("LLM 未配置：请设置 LLM_API_KEY 与 LLM_BASE_URL")
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url_v1)


def build_parse_messages(chunk_text: str) -> list[dict]:
    """加载 parse_system / parse_user 模板并组装字段抽取提示词。"""
    return load_messages([
        {"role": "system", "name": "parse_system"},
        {
            "role": "user",
            "name": "parse_user",
            "format": {"all_fields": ALL_FIELDS, "chunk_text": chunk_text},
        },
    ])


def _call_llm(chunk_text: str) -> list[dict]:
    """调用 LLM 并解析输出，失败自动重试 1 次（指数退避）。"""
    client = _get_client()
    settings = get_settings()
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = create_structured(
                client,
                settings.llm_model,
                build_parse_messages(chunk_text),
                "contract_fields",
                _FIELDS_SCHEMA,
            )
            break
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    else:
        raise RuntimeError(f"LLM 调用失败（已重试 1 次）：{last_error}")
    content = response.choices[0].message.content
    payload = json.loads(content)
    if isinstance(payload, dict):
        for key in ("fields", "data", "result"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
        else:
            items = []
            for name, value in payload.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("field_name", name)
                    items.append(item)
                else:
                    items.append(
                        {
                            "field_name": name,
                            "field_value": value,
                            "raw_text": "",
                            "page_no": 0,
                            "extract_status": "extracted" if value else "missing",
                        }
                    )
            payload = items
    if not isinstance(payload, list):
        raise RuntimeError("LLM 输出结构不是 JSON 数组")
    return payload


def validate_parse_result(fields: list[ParseField]) -> tuple[str, str | None]:
    """三层判定：全部 missing → failed；部分缺失 → success + missing。"""
    if not any(field.extract_status == "extracted" for field in fields):
        return "failed", "LLM 返回空结果或全部字段缺失"
    return "success", None


def _pick_best(candidates: list[dict]) -> dict:
    """重复字段按证据质量选最优。"""
    valid = [item for item in candidates if item.get("extract_status") == "extracted" and item.get("field_value")]
    if not valid:
        return {"field_value": "", "raw_text": "", "page_no": 0, "extract_status": "missing"}
    best = valid[0]
    for item in valid[1:]:
        if item["field_name"] == "金额":
            if _to_amount(item) > _to_amount(best):
                best = item
        elif len(item.get("raw_text", "")) > len(best.get("raw_text", "")):
            best = item
    return best


def _to_amount(item: dict) -> float:
    """从金额原文提取数值。"""
    import re

    numbers = re.findall(r"[\d,]+(?:\.\d+)?", item.get("field_value", ""))
    return float(numbers[0].replace(",", "")) if numbers else 0.0


def extract_contract_fields(chunks: list[str], llm=None) -> ContractParseResult:
    """对候选文本分块抽取 16 字段并合并。"""
    if not chunks:
        raise ValueError("候选文本为空")
    merged: dict[str, list[dict]] = {field: [] for field in ALL_FIELDS}
    for chunk in chunks:
        payload = _call_llm(chunk)
        for item in payload:
            name = item.get("field_name")
            if name in merged:
                merged[name].append(item)
    fields: list[ParseField] = []
    for name in ALL_FIELDS:
        best = _pick_best(merged[name])
        fields.append(
            ParseField(
                field_name=name,
                field_value=best.get("field_value", ""),
                raw_text=best.get("raw_text", ""),
                page_no=int(best.get("page_no", 0) or 0),
                extract_status=best.get("extract_status", "missing"),
            )
        )
    basic_info = {field.field_name: field.field_value for field in fields[:8]}
    clauses = {field.field_name: {"raw_text": field.raw_text, "page_no": field.page_no} for field in fields[8:]}
    parse_status, parse_error = validate_parse_result(fields)
    return ContractParseResult(
        basic_info=basic_info,
        clauses=clauses,
        fields=fields,
        parse_status=parse_status,
        parse_error=parse_error,
    )
