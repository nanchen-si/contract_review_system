"""评论生成代理。"""

import json
import logging

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger("writeback_agent")


def generate_comment(review_result: dict) -> str:
    """生成回写评论：总风险 + 关注点 + 摘要。"""
    settings = get_settings()
    if settings.llm_api_key and settings.llm_base_url.startswith(("http://", "https://")):
        try:
            client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url_v1)
            messages = [
                {
                    "role": "system",
                    "content": "你是合同审查评论撰写助手。输出中文回写评论：总风险 + 审批关注点 + 摘要；只引用已确认证据，不代替人工审批。输出 JSON 对象：{\"comment_text\": \"评论内容\"}。",
                },
                {
                    "role": "user",
                    "content": f"审查结果：{review_result}",
                },
            ]
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                response_format={"type": "json_object"},
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
