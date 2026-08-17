"""命中查询与人工复核接口。"""

from fastapi import APIRouter
from sqlalchemy import select

from app.db import get_session
from app.models.rule import ReviewRule, RuleHit
from app.schemas.common import ApiResponse
from app.schemas.hit import HitOut

router = APIRouter(prefix="/api/hits", tags=["hits"])


@router.get("", response_model=ApiResponse[list[HitOut]])
def list_hits(task_id: int | None = None, rule_id: int | None = None, risk_level: str | None = None):
    """按任务/规则/风险筛选命中。"""
    filters = []
    if task_id is not None:
        filters.append(RuleHit.task_id == task_id)
    if rule_id is not None:
        filters.append(RuleHit.rule_id == rule_id)
    if risk_level is not None:
        filters.append(ReviewRule.risk_level == risk_level)
    with next(get_session()) as db:
        rows = db.execute(
            select(RuleHit, ReviewRule)
            .join(ReviewRule, ReviewRule.id == RuleHit.rule_id)
            .where(*filters)
            .order_by(RuleHit.id.desc())
        ).all()
    return ApiResponse(
        code=0,
        message="ok",
        data=[
            HitOut(
                id=hit.id,
                task_id=hit.task_id,
                rule_id=hit.rule_id,
                rule_name=rule.rule_name,
                risk_level=rule.risk_level,
                evidence_text=hit.evidence_text,
                evidence_position=hit.evidence_position,
                hit_status=hit.hit_status,
            )
            for hit, rule in rows
        ],
    )


def _reserved(hit_id: int, action: str):
    """框架预留接口，demo 返回未启用。"""
    return ApiResponse(code=0, message=f"{action} 未启用（框架预留）", data=None)


@router.post("/{hit_id}/confirm", response_model=ApiResponse)
def confirm_hit(hit_id: int):
    """人工确认命中（预留）。"""
    return _reserved(hit_id, "confirm")


@router.post("/{hit_id}/ignore", response_model=ApiResponse)
def ignore_hit(hit_id: int):
    """忽略命中（预留）。"""
    return _reserved(hit_id, "ignore")
