"""日志相关请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogOut(BaseModel):
    """日志输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int | None = None
    log_level: str
    log_type: str
    log_content: str
    create_time: datetime


class LogQuery(BaseModel):
    """日志查询参数。"""

    task_id: int | None = None
    log_level: str | None = None
    log_type: str | None = None
    page: int = 1
    size: int = 20
