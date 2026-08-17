"""解析类工具。"""

from dataclasses import asdict

from app.agents.parse_agent import extract_contract_fields
from app.config import get_settings
from app.db import get_session
from app.models.approval import ApprovalAttachment
from app.services.clause_splitter import (
    chunk_for_llm,
    clean_document_text,
    filter_relevant_text,
    split_markdown_sections,
    to_markdown,
)
from app.services.parse_service import extract_document_text, save_parse_result


def parse_contract_document(document_id: int) -> dict:
    """按附件记录解析合同，返回结构化字段、原文片段与定位信息。"""
    with next(get_session()) as db:
        attachment = db.get(ApprovalAttachment, document_id)
        if attachment is None:
            raise ValueError(f"附件记录不存在: {document_id}")
        task_id = attachment.task_id
        file_path = attachment.file_path

    document_text = extract_document_text(file_path)
    cleaned = clean_document_text(document_text)
    md = to_markdown(cleaned)
    sections = split_markdown_sections(md)
    relevant = filter_relevant_text(sections)
    chunks = chunk_for_llm(relevant, get_settings().max_llm_chars)
    result = extract_contract_fields(chunks)
    payload = {
        "basic_info": result.basic_info,
        "clauses": result.clauses,
        "fields": [asdict(field) for field in result.fields],
        "parse_status": result.parse_status,
        "parse_error": result.parse_error,
    }
    save_parse_result(task_id, payload)
    return payload
