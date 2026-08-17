"""任务相关请求/响应模型。"""

from typing import Any

from pydantic import BaseModel


class TaskSummary(BaseModel):
    """任务列表项。"""

    id: int
    approval_code: str
    approval_title: str
    applicant_name: str
    task_status: str
    write_status: str


class TaskDetail(BaseModel):
    """任务详情聚合：附件、解析、命中、结果。"""

    id: int
    approval_code: str
    approval_title: str
    applicant_name: str
    task_status: str
    write_status: str
    attachments: list[Any] = []
    parse: Any | None = None
    hits: list[Any] = []
    result: Any | None = None


class TaskStatusFilter(BaseModel):
    """任务列表筛选参数。"""

    task_status: str | None = None
    page: int = 1
    size: int = 20
