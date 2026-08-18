"""集中加载提示词模板。

文件名以 .txt 存放于本目录，调用方通过名称引用，无需在代码里维护提示词正文。
模板支持 Python str.format 占位（如 {chunk_text}），load_messages 会按 spec 渲染。
"""

from app.prompt.loader import (
    PROMPT_DIR,
    MessageSpec,
    list_prompts,
    load_messages,
    load_prompt,
    render_prompt,
)

__all__ = [
    "PROMPT_DIR",
    "MessageSpec",
    "list_prompts",
    "load_messages",
    "load_prompt",
    "render_prompt",
]
