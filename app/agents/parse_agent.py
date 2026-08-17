"""LLM 字段抽取代理。"""

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.config import get_settings

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
    """构造字段抽取提示词，写明字段清单、金额规则与重复字段优先级。"""
    system = (
        "你是合同审查系统的字段抽取器。只依据合同原文抽取字段，禁止编造；"
        "缺失字段标记 missing。字段名必须严格使用给定清单。"
    )
    user = (
        "请从以下合同文本中抽取字段。\n"
        f"字段清单：{ALL_FIELDS}\n"
        "规则：\n"
        "1. 金额只提取含具体数值的原文，如“合同总金额为人民币 1,200,000 元”；"
        "仅出现“金额”二字不提取；多条候选取金额最大者。\n"
        "2. 合同标题、合同编号等唯一字段只保留一条，原文上下文最完整者优先。\n"
        "3. 每个字段输出 field_name、field_value、raw_text、page_no、extract_status，"
        "extract_status 只能为 extracted 或 missing。\n"
        "输出 JSON 对象：{\"fields\": [字段数组]}，不要输出其他内容。\n\n"
        f"合同文本：\n{chunk_text}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _call_llm(chunk_text: str) -> list[dict]:
    """调用一次 LLM，解析 JSON 数组输出。"""
    client = _get_client()
    settings = get_settings()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=build_parse_messages(chunk_text),
        response_format={"type": "json_object"},
    )
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
    return ContractParseResult(
        basic_info=basic_info,
        clauses=clauses,
        fields=fields,
        parse_status="success",
    )
