"""规则维护接口。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import require_admin
from app.db import get_session
from app.models.rule import ReviewRule
from app.schemas.common import ApiResponse
from app.schemas.rule import RuleCreate, RuleOut, RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=ApiResponse[list[RuleOut]])
def list_rules():
    """规则列表。"""
    with next(get_session()) as db:
        rules = db.scalars(
            select(ReviewRule).where(ReviewRule.is_deleted == 0).order_by(ReviewRule.id)
        ).all()
    return ApiResponse(code=0, message="ok", data=[RuleOut.model_validate(rule) for rule in rules])


@router.post("", response_model=ApiResponse[RuleOut])
def create_rule(payload: RuleCreate, _=Depends(require_admin)):
    """新增规则（admin）。"""
    with next(get_session()) as db:
        exists = db.scalar(select(ReviewRule).where(ReviewRule.rule_code == payload.rule_code))
        if exists is not None:
            raise HTTPException(status_code=400, detail="规则编码已存在")
        rule = ReviewRule(**payload.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return ApiResponse(code=0, message="ok", data=RuleOut.model_validate(rule))


@router.put("/{rule_id}", response_model=ApiResponse[RuleOut])
def update_rule(rule_id: int, payload: RuleUpdate, _=Depends(require_admin)):
    """更新规则（admin）。"""
    with next(get_session()) as db:
        rule = db.get(ReviewRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=400, detail="规则不存在")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        db.commit()
        db.refresh(rule)
    return ApiResponse(code=0, message="ok", data=RuleOut.model_validate(rule))


@router.delete("/{rule_id}", response_model=ApiResponse[dict])
def delete_rule(rule_id: int, _=Depends(require_admin)):
    """逻辑删除规则（admin）。"""
    with next(get_session()) as db:
        rule = db.get(ReviewRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=400, detail="规则不存在")
        rule.is_deleted = 1
        db.commit()
    return ApiResponse(code=0, message="ok", data={"id": rule_id})
