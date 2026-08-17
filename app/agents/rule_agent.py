"""LLM 语义规则判断。"""

import json

from openai import OpenAI

from app.agents.llm import create_structured
from app.config import get_settings
from app.services.log_service import write_task_log
from app.services.rule_service import HitMatch

_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "integer"},
        "hit": {"type": "boolean"},
        "evidence_text": {"type": "string"},
        "evidence_position": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["rule_id", "hit", "evidence_text", "evidence_position", "reason"],
    "additionalProperties": False,
}

_KEEP_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["keep", "reason"],
    "additionalProperties": False,
}


def _get_client() -> OpenAI:
    """按 .env 创建 OpenAI 兼容客户端。"""
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_base_url.startswith(("http://", "https://")):
        raise RuntimeError("LLM 未配置：无法执行语义规则判断")
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url_v1)


def _judge_one(rule, clause_text: str) -> dict:
    """判断单条语义规则。"""
    client = _get_client()
    settings = get_settings()
    messages = [
        {
            "role": "system",
            "content": "你是合同风险审查员。判断规则是否命中，只引用原文证据；无法判断时 hit=false。",
        },
        {
            "role": "user",
            "content": (
                f"规则：{rule.rule_name}（{rule.match_text}）\n"
                f"条款文本：\n{clause_text}\n"
                "输出 JSON：{\"rule_id\": 0, \"hit\": false, \"evidence_text\": \"\", "
                "\"evidence_position\": \"\", \"reason\": \"\"}"
            ),
        },
    ]
    response = create_structured(
        client,
        settings.llm_model,
        messages,
        "semantic_verdict",
        _VERDICT_SCHEMA,
    )
    return json.loads(response.choices[0].message.content)


def judge_semantic_rules(context: dict, llm_rules: list) -> list[HitMatch]:
    """逐条语义判断，返回命中结果；LLM 不可用时跳过并记录日志。"""
    if not llm_rules:
        return []
    clause_text = "\n".join(
        str(clause.get("raw_text", "")) if isinstance(clause, dict) else str(clause)
        for clause in context.get("clauses", {}).values()
    )
    hits: list[HitMatch] = []
    try:
        for rule in llm_rules:
            verdict = _judge_one(rule, clause_text)
            if verdict.get("hit"):
                hits.append(
                    HitMatch(
                        rule_id=rule.id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        risk_level=rule.risk_level,
                        evidence_text=verdict.get("evidence_text", "") or verdict.get("reason", ""),
                        evidence_position=verdict.get("evidence_position", "条款语义判断"),
                        suggestion_text=rule.suggestion_text or "",
                    )
                )
    except Exception as exc:
        write_task_log(None, "warn", "rule", f"LLM 语义规则判断失败，已跳过：{exc}")
    return hits


def _judge_recheck(hit: HitMatch, clause_text: str) -> dict:
    """让 LLM 复核一条代码命中是否成立。"""
    client = _get_client()
    settings = get_settings()
    messages = [
        {
            "role": "system",
            "content": "你是合同风险审查复核员。判断命中证据是否真实支持该规则，只依据原文判断。输出 JSON 对象：{\"keep\": true, \"reason\": \"\"}。",
        },
        {
            "role": "user",
            "content": (
                f"规则：{hit.rule_name}\n"
                f"命中证据：{hit.evidence_text}\n"
                f"合同文本：\n{clause_text}"
            ),
        },
    ]
    response = create_structured(
        client,
        settings.llm_model,
        messages,
        "hit_recheck",
        _KEEP_SCHEMA,
    )
    return json.loads(response.choices[0].message.content)


def review_code_hits(hits: list[HitMatch], context: dict, llm=None) -> list[HitMatch]:
    """LLM 复核代码命中，过滤明显误报；LLM 不可用时原样保留。"""
    if not hits:
        return []
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_base_url.startswith(("http://", "https://")):
        return hits
    clause_text = "\n".join(
        str(clause.get("raw_text", "")) if isinstance(clause, dict) else str(clause)
        for clause in context.get("clauses", {}).values()
    )
    kept: list[HitMatch] = []
    try:
        for hit in hits:
            verdict = _judge_recheck(hit, clause_text)
            if verdict.get("keep") is not False:
                kept.append(hit)
    except Exception as exc:
        write_task_log(None, "warn", "rule", f"LLM 代码命中复核失败，保留全部命中：{exc}")
        return hits
    return kept or hits
