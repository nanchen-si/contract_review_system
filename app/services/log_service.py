"""任务日志持久化与分页查询。"""

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.db import get_session
from app.models.log import TaskLog
from app.schemas.common import PageResult

logger = get_logger("log_service")


def write_task_log(task_id: int | None, log_level: str, log_type: str, log_content: str):
    """写一条 task_logs。"""
    with next(get_session()) as db:
        db.add(
            TaskLog(
                task_id=task_id,
                log_level=log_level,
                log_type=log_type,
                log_content=log_content,
            )
        )
        db.commit()


def list_task_logs(
    task_id: int | None = None,
    log_level: str | None = None,
    log_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PageResult:
    """分页查询日志。"""
    filters = []
    if task_id is not None:
        filters.append(TaskLog.task_id == task_id)
    if log_level is not None:
        filters.append(TaskLog.log_level == log_level)
    if log_type is not None:
        filters.append(TaskLog.log_type == log_type)
    base = select(TaskLog).where(*filters)
    with next(get_session()) as db:
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = db.scalars(
            base.order_by(TaskLog.id.desc()).offset((page - 1) * size).limit(size)
        ).all()
    return PageResult(items=list(items), total=total, page=page, size=size)
