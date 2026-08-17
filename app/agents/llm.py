"""LLM 结构化输出封装：优先 JSON Schema，兼容端点回退 json_object。"""

import logging

from openai import BadRequestError
from openai import OpenAI

logger = logging.getLogger("llm")


def json_schema_format(name: str, schema: dict) -> dict:
    """构造 OpenAI 兼容的 json_schema response_format。"""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema,
        },
    }


def create_structured(
    client: OpenAI,
    model: str,
    messages: list[dict],
    name: str,
    schema: dict,
):
    """先用 json_schema 调用；端点不支持时回退 json_object 并记录日志。"""
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=json_schema_format(name, schema),
        )
    except BadRequestError:
        logger.warning("端点不支持 json_schema，已回退 json_object：%s", name)
        return client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
