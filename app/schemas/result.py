"""审查结果响应模型。"""

from pydantic import BaseModel


class ResultOut(BaseModel):
    """审查结果输出。"""

    id: int
    task_id: int
    overall_risk_level: str
    summary_text: str
    focus_points_json: dict | None = None
    comment_text: str | None = None
