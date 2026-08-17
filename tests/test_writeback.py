"""回写服务单元测试。"""

from sqlalchemy import select

from app.db import get_session
from app.models.result import ReviewResult
from app.services import writeback_service


def test_prepare_writeback_persists_comment(db_session, monkeypatch):
    """评论必须真实写入 review_results.comment_text。"""
    with next(get_session()) as db:
        review = ReviewResult(
            task_id=1,
            overall_risk_level="high",
            summary_text="摘要",
            focus_points_json=[],
        )
        db.add(review)
        db.commit()
    monkeypatch.setattr(writeback_service, "generate_comment", lambda payload: "评论内容")
    comment = writeback_service.prepare_writeback(1)
    assert comment == "评论内容"
    with next(get_session()) as db:
        saved = db.scalar(select(ReviewResult).where(ReviewResult.task_id == 1))
        assert saved.comment_text == "评论内容"
