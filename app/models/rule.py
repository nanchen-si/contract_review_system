"""审查规则与命中记录模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReviewRule(Base):
    """审查规则，match_mode 决定 regex/numeric/llm 匹配方式。"""

    __tablename__ = "review_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True)
    rule_name: Mapped[str] = mapped_column(String(128))
    risk_level: Mapped[str] = mapped_column(String(8))
    rule_status: Mapped[str] = mapped_column(String(8))
    match_mode: Mapped[str] = mapped_column(String(16))
    match_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)


class RuleHit(Base):
    """规则命中：证据原文、位置与人工确认状态。"""

    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger)
    rule_id: Mapped[int] = mapped_column(BigInteger)
    evidence_text: Mapped[str] = mapped_column(Text)
    evidence_position: Mapped[str] = mapped_column(String(255))
    hit_status: Mapped[str] = mapped_column(String(16))
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)
