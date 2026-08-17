"""结果类工具。"""

from app.services.rule_service import save_review_result as _save_review_result
from app.services.writeback_service import writeback_by_review


def save_review_result(
    case_id: int,
    overall_risk_level: str,
    summary_text: str,
    focus_points_json: list,
    comment_text: str,
):
    """保存审查结果。"""
    return _save_review_result(case_id, overall_risk_level, summary_text, focus_points_json, comment_text)


def write_approval_comment(instance_id: str, review_id: int) -> str:
    """生成评论并回写审批系统。"""
    return writeback_by_review(review_id, instance_id=instance_id)
