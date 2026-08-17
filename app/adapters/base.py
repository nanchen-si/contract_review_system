"""审批系统适配层数据模型与统一接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AttachmentInfo:
    """附件信息。"""

    attachment_id: str
    file_name: str
    file_type: str


@dataclass(slots=True)
class ApprovalRecord:
    """待办列表项。"""

    approval_code: str
    approval_title: str
    applicant_name: str
    application_time: datetime
    attachment_count: int


@dataclass(slots=True)
class ApprovalDetail:
    """审批详情。"""

    instance_id: str
    approval_code: str
    approval_title: str
    applicant_name: str
    application_time: datetime
    form_data: dict
    attachments: list[AttachmentInfo]
    status: str


@dataclass(slots=True)
class DownloadResult:
    """下载结果。"""

    file_path: str
    file_checksum: str


@dataclass(slots=True)
class WritebackResult:
    """回写结果。"""

    success: bool
    response_text: str


class ApprovalAdapter(ABC):
    """审批系统统一接口，Mock 与 Real 实现此接口。"""

    @abstractmethod
    def list_pending(self, limit: int) -> list[ApprovalRecord]:
        """拉取待办。"""

    @abstractmethod
    def get_detail(self, instance_id: str) -> ApprovalDetail:
        """获取审批详情。"""

    @abstractmethod
    def download(self, instance_id: str, attachment_id: str, file_name: str) -> DownloadResult:
        """下载附件。"""

    @abstractmethod
    def write_comment(self, instance_id: str, review_id: int) -> WritebackResult:
        """回写评论。"""
