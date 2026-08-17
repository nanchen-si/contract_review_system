"""章节识别与 Markdown 中间格式。"""

import re

from app.config import get_settings
from app.services.parse_service import DocumentText

_PAGE_MARKER = "<!-- page: {page_no} -->"
_PAGE_MARKER_RE = re.compile(r"^<!-- page: (\d+) -->$")
_CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百千0-9]+[章节条][：、:\s]")
_NUMBERED_RE = re.compile(r"^[一二三四五六七八九十]+、")
_HEADING_END = ("。", "；", "，", ".")


def clean_document_text(document_text: DocumentText) -> DocumentText:
    """去页码、空行与重复抬头，压缩空白。"""
    pages = []
    for page in document_text.pages:
        lines = []
        for line in page.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.isdigit():
                continue
            if re.fullmatch(r"第\s*\d+\s*页", stripped):
                continue
            lines.append(stripped)
        pages.append(type(page)(page_no=page.page_no, text="\n".join(lines)))
    return DocumentText(file_path=document_text.file_path, pages=pages)


def _heading_score(line: str, keywords: list[str]) -> int:
    """三级信号中的文本模式评分。"""
    score = 0
    if _CHAPTER_RE.match(line):
        score += 50
    if _NUMBERED_RE.match(line):
        score += 30
    if any(keyword in line for keyword in keywords):
        score += 40
    if len(line) <= get_settings().heading_max_length and not line.endswith(_HEADING_END):
        score += 10
    return score


def detect_headings(document_text: DocumentText) -> list[str]:
    """按 HEADING_SCORE_THRESHOLD 识别标题行。"""
    settings = get_settings()
    threshold = settings.heading_score_threshold
    headings = []
    for page in document_text.pages:
        for line in page.text.splitlines():
            if _heading_score(line, settings.clause_keyword_list) >= threshold:
                headings.append(line)
    return headings


def to_markdown(document_text: DocumentText) -> str:
    """标题行加 #，生成内存 Markdown 中间格式。"""
    settings = get_settings()
    lines: list[str] = []
    for page in document_text.pages:
        lines.append(_PAGE_MARKER.format(page_no=page.page_no))
        for line in page.text.splitlines():
            if _heading_score(line, settings.clause_keyword_list) >= settings.heading_score_threshold:
                lines.append(f"# {line}")
            else:
                lines.append(line)
    return "\n".join(lines)


def split_markdown_sections(md: str) -> list[dict]:
    """按 # 标题切章节块，无标题时退化为按页分块。"""
    sections: list[dict] = []
    current: dict | None = None
    paragraph_index = 0
    has_heading = any(line.startswith("# ") for line in md.splitlines())
    for line in md.splitlines():
        marker = _PAGE_MARKER_RE.match(line)
        if marker:
            page_no = int(marker.group(1))
            if current is None:
                current = {
                    "clause_name": f"第 {page_no} 页",
                    "raw_text": "",
                    "page_no": page_no,
                    "paragraph_index": paragraph_index,
                    "extract_status": "extracted",
                    "is_heading": False,
                }
            else:
                current["page_no"] = page_no
            continue
        if line.startswith("# "):
            if current is not None and current["raw_text"]:
                sections.append(current)
            name = line[2:].strip()
            raw_text = name
            if "：" in name:
                name, raw_text = name.split("：", 1)
                raw_text = line[2:].strip()
            current = {
                "clause_name": name,
                "raw_text": raw_text,
                "page_no": current["page_no"] if current else 1,
                "paragraph_index": paragraph_index,
                "extract_status": "extracted",
                "is_heading": True,
            }
            paragraph_index += 1
            continue
        if current is None:
            current = {
                "clause_name": "正文",
                "raw_text": "",
                "page_no": 1,
                "paragraph_index": paragraph_index,
                "extract_status": "extracted",
            }
        current["raw_text"] = (current["raw_text"] + "\n" + line).strip()
        paragraph_index += 1
    if current is not None and (current["raw_text"] or current.get("is_heading")):
        sections.append(current)
    if not sections and not has_heading:
        return [{"clause_name": "全文", "raw_text": md, "page_no": 1, "paragraph_index": 0, "extract_status": "extracted"}]
    return sections


def filter_relevant_text(sections: list[dict]) -> list[dict]:
    """保留基本信息候选区（首个块）与 8 个条款命中块。"""
    settings = get_settings()
    keywords = settings.clause_keyword_list
    kept: list[dict] = []
    for index, section in enumerate(sections):
        if index == 0:
            kept.append(section)
            continue
        if any(keyword in section["clause_name"] for keyword in keywords):
            kept.append(section)
    return kept


def chunk_for_llm(sections: list[dict], max_chars: int) -> list[str]:
    """按 MAX_LLM_CHARS 分块，每块保留章节标题。"""
    chunks: list[str] = []
    buffer: list[str] = []
    size = 0
    for section in sections:
        block = f"# {section['clause_name']}\n{section['raw_text']}"
        if size + len(block) > max_chars and buffer:
            chunks.append("\n\n".join(buffer))
            buffer = []
            size = 0
        buffer.append(block)
        size += len(block)
    if buffer:
        chunks.append("\n\n".join(buffer))
    return chunks
