"""全链路任务日志模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskLog(Base):
    """任务日志：级别、类型、内容，task_id 可空。"""

    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_level: Mapped[str] = mapped_column(String(8))
    log_type: Mapped[str] = mapped_column(String(16))
    log_content: Mapped[str] = mapped_column(Text)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
