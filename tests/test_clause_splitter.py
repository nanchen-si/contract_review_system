"""章节识别与 Markdown 中间格式测试。"""

from app.services.clause_splitter import (
    chunk_for_llm,
    clean_document_text,
    detect_headings,
    filter_relevant_text,
    split_markdown_sections,
    to_markdown,
)
from app.services.parse_service import DocumentPage, DocumentText


def _sample() -> DocumentText:
    return DocumentText(
        file_path="sample.docx",
        pages=[
            DocumentPage(
                page_no=1,
                text="供应商采购合同\n合同编号：HT-2026-0088\n第三条 付款条款：预付款 60%\n",
            )
        ],
    )


def test_detect_and_split_headings():
    """标题识别与章节切分。"""
    text = _sample()
    headings = detect_headings(text)
    assert "第三条 付款条款：预付款 60%" in headings
    md = to_markdown(text)
    sections = split_markdown_sections(md)
    assert any(section["clause_name"].startswith("第三条") for section in sections)


def test_filter_and_chunk():
    """过滤与分块。"""
    md = to_markdown(_sample())
    sections = split_markdown_sections(md)
    relevant = filter_relevant_text(sections)
    assert relevant
    chunks = chunk_for_llm(relevant, max_chars=50)
    assert chunks


def test_clean_document_text():
    """清洗页码与空行。"""
    dirty = DocumentText(
        file_path="x.pdf",
        pages=[DocumentPage(page_no=1, text="12\n\n第 1 页\n合同编号：HT-1\n")],
    )
    cleaned = clean_document_text(dirty)
    assert "12" not in cleaned.pages[0].text
    assert "合同编号" in cleaned.pages[0].text
