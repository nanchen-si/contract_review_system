"""解析结果响应模型。"""

from pydantic import BaseModel


class ParseOut(BaseModel):
    """解析结果输出。"""

    id: int
    task_id: int
    basic_info_json: dict | None = None
    clause_info_json: dict | None = None
    parse_status: str
    parse_error: str | None = None
