"""规则类工具。"""

from app.services.rule_service import run_review_pipeline


def run_contract_rules(case_id: int) -> dict:
    """执行规则审查流水线，返回命中结果与风险结论。"""
    return run_review_pipeline(case_id)
