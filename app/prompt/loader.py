"""提示词加载与渲染。

设计原则：
- 提示词正文一律放在本目录下的 .txt 文件中，文件名即引用名。
- 模板使用 Python str.format 占位，load_messages 按 spec 渲染后再组装 OpenAI 消息。
- 单文件加载用 load_prompt(name)；多轮消息用 load_messages(spec)。
- 文件缺失或占位缺失时给出明确错误，便于排查。
"""

from pathlib import Path
from typing import Any, TypedDict

PROMPT_DIR: Path = Path(__file__).resolve().parent


class MessageSpec(TypedDict, total=False):
    """load_messages 的单项规格。

    role: "system" | "user" | "assistant"
    name: 模板文件名（不含扩展名）
    format: 传给 str.format 的关键字字典；缺省则原样返回。
    """

    role: str
    name: str
    format: dict[str, Any]


def _resolve(name: str) -> Path:
    """拼出模板绝对路径，缺失抛错。"""
    if not name.endswith(".txt"):
        name = name + ".txt"
    path = PROMPT_DIR / name
    if not path.is_file():
        raise FileNotFoundError(
            f"提示词模板不存在：{name}（搜索目录 {PROMPT_DIR}）"
        )
    return path


def load_prompt(name: str) -> str:
    """读取原始模板文本，不做格式化。"""
    return _resolve(name).read_text(encoding="utf-8").strip()


def render_prompt(name: str, **kwargs: Any) -> str:
    """读取模板并用 str.format 渲染（始终调用以处理 {{ }} 转义）。"""
    template = load_prompt(name)
    try:
        return template.format(**kwargs)
    except KeyError as exc:
        raise KeyError(
            f"提示词 {name} 缺少占位变量 {exc.args[0]!r}；"
            f"模板占位：{[p for p in _placeholder_names(template)]}"
        ) from exc


def load_messages(spec: list[MessageSpec]) -> list[dict[str, str]]:
    """按 spec 顺序加载并渲染一组 OpenAI 兼容消息。

    示例：
        load_messages([
            {"role": "system", "name": "parse_system"},
            {"role": "user", "name": "parse_user",
             "format": {"all_fields": ALL_FIELDS, "chunk_text": text}},
        ])
    """
    messages: list[dict[str, str]] = []
    for item in spec:
        text = render_prompt(item["name"], **(item.get("format") or {}))
        messages.append({"role": item["role"], "content": text})
    return messages


def list_prompts() -> list[str]:
    """列出所有可用的提示词名（不含扩展名），供调试/自检使用。"""
    return sorted(p.stem for p in PROMPT_DIR.glob("*.txt"))


def _placeholder_names(template: str) -> set[str]:
    """尽量列举 str.format 占位名（不做完整语法分析，简单够用即可）。"""
    import re

    return set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template))
