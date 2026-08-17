"""ORM 模型统一导出，导入本模块即注册全部表到 Base.metadata。"""

from app.models.approval import ApprovalAttachment, ApprovalTask
from app.models.base import Base
from app.models.log import TaskLog
from app.models.parse import ContractParse
from app.models.result import CommentLog, ReviewResult
from app.models.rule import ReviewRule, RuleHit
from app.models.user import User

__all__ = [
    "ApprovalAttachment",
    "ApprovalTask",
    "Base",
    "CommentLog",
    "ContractParse",
    "ReviewResult",
    "ReviewRule",
    "RuleHit",
    "TaskLog",
    "User",
]
