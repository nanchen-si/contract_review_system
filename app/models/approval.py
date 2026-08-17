"""审批任务与附件模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ApprovalTask(Base):
    """审批任务，approval_code 为去重键。"""

    __tablename__ = "approval_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_code: Mapped[str] = mapped_column(String(64), unique=True)
    approval_title: Mapped[str] = mapped_column(String(255))
    applicant_name: Mapped[str] = mapped_column(String(64))
    task_status: Mapped[str] = mapped_column(String(16))
    write_status: Mapped[str] = mapped_column(String(16))
    create_user_id: Mapped[int] = mapped_column(BigInteger)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)


class ApprovalAttachment(Base):
    """审批附件，记录下载状态与本地路径。"""

    __tablename__ = "approval_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger)
    attachment_id: Mapped[str] = mapped_column(String(64))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(32))
    file_path: Mapped[str] = mapped_column(String(512))
    download_status: Mapped[str] = mapped_column(String(16))
    create_user_id: Mapped[int] = mapped_column(BigInteger)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
