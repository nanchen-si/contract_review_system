"""合同解析结果模型。"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContractParse(Base):
    """解析结果：基本信息、条款信息、解析状态与失败原因。"""

    __tablename__ = "contract_parses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger)
    basic_info_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    clause_info_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(16))
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)
