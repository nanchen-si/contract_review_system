"""命中相关请求/响应模型。"""

from pydantic import BaseModel


class HitOut(BaseModel):
    """命中输出。"""

    id: int
    task_id: int
    rule_id: int
    rule_name: str
    risk_level: str
    evidence_text: str
    evidence_position: str
    hit_status: str


class HitConfirmRequest(BaseModel):
    """人工确认命中请求。"""

    hit_status: str
