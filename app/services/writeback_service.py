"""评论生成、回写与状态记录。"""

from sqlalchemy import select

from app.adapters.factory import get_adapter
from app.agents.writeback_agent import generate_comment
from app.db import get_session
from app.models.approval import ApprovalTask
from app.models.result import CommentLog, ReviewResult
from app.services.log_service import write_task_log


def _get_review(task_id: int) -> ReviewResult | None:
    with next(get_session()) as db:
        return db.scalar(select(ReviewResult).where(ReviewResult.task_id == task_id))


def prepare_writeback(task_id: int) -> str:
    """生成评论并写入 review_results.comment_text。"""
    review = _get_review(task_id)
    if review is None:
        raise RuntimeError(f"任务 {task_id} 无审查结果")
    comment = generate_comment(
        {
            "overall_risk_level": review.overall_risk_level,
            "summary_text": review.summary_text,
            "focus_points": review.focus_points_json or [],
        }
    )
    with next(get_session()) as db:
        review.comment_text = comment
        db.commit()
    return comment


def writeback(task_id: int):
    """调用适配层回写，更新 write_status 并写 comment_logs。"""
    comment = prepare_writeback(task_id)
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        review = db.scalar(select(ReviewResult).where(ReviewResult.task_id == task_id))
        if task is None or review is None:
            raise RuntimeError(f"任务 {task_id} 或审查结果不存在")
        instance_id = task.approval_code
        result = get_adapter().write_comment(instance_id, review.id)
        db.add(
            CommentLog(
                task_id=task_id,
                write_status="success" if result.success else "failed",
                write_response_text=result.response_text,
            )
        )
        task.write_status = "success" if result.success else "failed"
        db.commit()
    write_task_log(task_id, "info", "writeback", f"评论回写完成：{comment[:60]}")
    return comment


def retry_writeback(task_id: int) -> str:
    """回写失败重试。"""
    return writeback(task_id)


def writeback_by_review(review_id: int) -> str:
    """按 review_results.id 定位任务并回写。"""
    with next(get_session()) as db:
        review = db.get(ReviewResult, review_id)
        if review is None:
            raise RuntimeError(f"审查结果不存在: {review_id}")
        task_id = review.task_id
    return writeback(task_id)
