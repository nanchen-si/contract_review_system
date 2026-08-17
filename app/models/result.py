"""审查结果与回写日志模型。"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReviewResult(Base):
    """审查结果：总风险、摘要、关注点与回写评论。"""

    __tablename__ = "review_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger)
    overall_risk_level: Mapped[str] = mapped_column(String(8))
    summary_text: Mapped[str] = mapped_column(Text)
    focus_points_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    comment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)


class CommentLog(Base):
    """回写日志：记录每次回写的状态与响应。"""

    __tablename__ = "comment_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger)
    write_status: Mapped[str] = mapped_column(String(16))
    write_response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
