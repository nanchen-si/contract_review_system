"""规则相关请求/响应模型。"""

from pydantic import BaseModel, ConfigDict


class RuleCreate(BaseModel):
    """新增规则请求。"""

    rule_code: str
    rule_name: str
    risk_level: str
    rule_status: str
    match_mode: str
    match_text: str | None = None
    suggestion_text: str | None = None


class RuleUpdate(BaseModel):
    """更新规则请求，字段全部可选。"""

    model_config = ConfigDict(extra="forbid")

    rule_code: str | None = None
    rule_name: str | None = None
    risk_level: str | None = None
    rule_status: str | None = None
    match_mode: str | None = None
    match_text: str | None = None
    suggestion_text: str | None = None


class RuleOut(BaseModel):
    """规则输出。"""

    id: int
    rule_code: str
    rule_name: str
    risk_level: str
    rule_status: str
    match_mode: str
    match_text: str | None = None
    suggestion_text: str | None = None
