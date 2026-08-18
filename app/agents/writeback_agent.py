"""评论生成代理。"""

import json
import logging

from openai import OpenAI

from app.agents.llm import create_structured
from app.config import get_settings
from app.prompt import load_messages

logger = logging.getLogger("writeback_agent")

_COMMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "comment_text": {"type": "string"},
    },
    "required": ["comment_text"],
    "additionalProperties": False,
}


def generate_comment(review_result: dict) -> str:
    """生成回写评论：总风险 + 关注点 + 摘要。"""
    settings = get_settings()
    if settings.llm_api_key and settings.llm_base_url.startswith(("http://", "https://")):
        try:
            client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url_v1)
            messages = load_messages([
                {"role": "system", "name": "writeback_system"},
                {
                    "role": "user",
                    "name": "writeback_user",
                    "format": {"review_result": review_result},
                },
            ])
            response = create_structured(
                client,
                settings.llm_model,
                messages,
                "writeback_comment",
                _COMMENT_SCHEMA,
            )
            payload = json.loads(response.choices[0].message.content)
            return payload.get("comment_text") or str(payload)
        except Exception as exc:
            logger.warning("LLM 评论生成失败，使用模板兜底：%s", exc)
    return (
        f"总风险等级：{review_result.get('overall_risk_level', 'low')}\n"
        f"审批关注点：{'；'.join(review_result.get('focus_points', []) or [])}\n"
        f"摘要：{review_result.get('summary_text', '')}"
    )
