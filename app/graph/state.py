"""LangGraph 节点间共享的数据包。"""

from typing import Any, TypedDict


class ContractReviewState(TypedDict, total=False):
    """图状态，节点间只通过本结构交互。"""

    task_id: int
    instance_id: str
    approval_detail: Any
    attachment_path: str | None
    document_text: Any
    parse_result: dict | None
    hits: list
    review_result: dict | None
    comment_text: str | None
    writeback_result: Any
    error: str | None
    stage: str
