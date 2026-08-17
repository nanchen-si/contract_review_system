"""任务入库、去重、查询、重试与人工触发入口。"""

from sqlalchemy import func, select

from app.adapters.factory import get_adapter
from app.config import get_settings
from app.db import get_session
from app.models.approval import ApprovalAttachment, ApprovalTask
from app.models.log import TaskLog
from app.models.parse import ContractParse
from app.models.result import ReviewResult
from app.models.rule import RuleHit, ReviewRule
from app.schemas.common import PageResult
from app.schemas.task import TaskDetail, TaskSummary
from app.services.log_service import write_task_log


def create_task_from_approval(detail) -> ApprovalTask:
    """创建或更新任务（按 approval_code 去重）。"""
    with next(get_session()) as db:
        task = db.scalar(
            select(ApprovalTask).where(ApprovalTask.approval_code == detail.approval_code)
        )
        if task is None:
            task = ApprovalTask(
                approval_code=detail.approval_code,
                approval_title=detail.approval_title,
                applicant_name=detail.applicant_name,
                task_status="pending",
                write_status="not_written",
                create_user_id=1,
            )
            db.add(task)
        else:
            task.approval_title = detail.approval_title
            task.applicant_name = detail.applicant_name
        db.commit()
        db.refresh(task)
    return task


def ingest_pending_approvals() -> list[ApprovalTask]:
    """拉取待办并按 approval_code 去重（更新或创建）。"""
    adapter = get_adapter()
    tasks: list[ApprovalTask] = []
    for record in adapter.list_pending(100):
        detail = adapter.get_detail_by_code(record.approval_code)
        tasks.append(create_task_from_approval(detail))
    return tasks


def get_task_detail(task_id: int) -> TaskDetail:
    """聚合任务、附件、解析、命中、结果、日志，返回 TaskDetail。"""
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")
        attachments = list(
            db.scalars(select(ApprovalAttachment).where(ApprovalAttachment.task_id == task_id))
        )
        parse = db.scalar(select(ContractParse).where(ContractParse.task_id == task_id))
        result = db.scalar(select(ReviewResult).where(ReviewResult.task_id == task_id))
        hits = list(db.scalars(select(RuleHit).where(RuleHit.task_id == task_id)))
        rules = {rule.id: rule.rule_name for rule in db.scalars(select(ReviewRule))}
        logs = list(
            db.scalars(
                select(TaskLog)
                .where(TaskLog.task_id == task_id)
                .order_by(TaskLog.id.desc())
                .limit(20)
            )
        )
    return TaskDetail(
        id=task.id,
        approval_code=task.approval_code,
        approval_title=task.approval_title,
        applicant_name=task.applicant_name,
        task_status=task.task_status,
        write_status=task.write_status,
        attachments=[
            {
                "id": att.id,
                "attachment_id": att.attachment_id,
                "file_name": att.file_name,
                "file_type": att.file_type,
                "file_path": att.file_path,
                "download_status": att.download_status,
            }
            for att in attachments
        ],
        parse={
            "id": parse.id,
            "basic_info_json": parse.basic_info_json,
            "clause_info_json": parse.clause_info_json,
            "parse_status": parse.parse_status,
            "parse_error": parse.parse_error,
        }
        if parse is not None
        else None,
        hits=[
            {
                "id": hit.id,
                "rule_id": hit.rule_id,
                "rule_name": rules.get(hit.rule_id, ""),
                "evidence_text": hit.evidence_text,
                "evidence_position": hit.evidence_position,
                "hit_status": hit.hit_status,
            }
            for hit in hits
        ],
        result={
            "id": result.id,
            "overall_risk_level": result.overall_risk_level,
            "summary_text": result.summary_text,
            "focus_points_json": result.focus_points_json,
            "comment_text": result.comment_text,
        }
        if result is not None
        else None,
        logs=[
            {
                "id": log.id,
                "log_level": log.log_level,
                "log_type": log.log_type,
                "log_content": log.log_content,
                "create_time": log.create_time.isoformat(),
            }
            for log in logs
        ],
    )


def list_tasks(task_status: str | None = None, page: int = 1, size: int = 20) -> PageResult:
    """分页查询任务。"""
    filters = []
    if task_status is not None:
        filters.append(ApprovalTask.task_status == task_status)
    base = select(ApprovalTask).where(*filters)
    with next(get_session()) as db:
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        tasks = db.scalars(
            base.order_by(ApprovalTask.id.desc()).offset((page - 1) * size).limit(size)
        ).all()
    items = [
        TaskSummary(
            id=task.id,
            approval_code=task.approval_code,
            approval_title=task.approval_title,
            applicant_name=task.applicant_name,
            task_status=task.task_status,
            write_status=task.write_status,
        )
        for task in tasks
    ]
    return PageResult(items=items, total=total, page=page, size=size)


def retry_task(task_id: int) -> ApprovalTask:
    """blocked 任务重试：按失败点回 parsing/reviewing，受 MAX_RETRY_COUNT 限制。"""
    settings = get_settings()
    with next(get_session()) as db:
        retry_count = db.scalar(
            select(func.count())
            .select_from(TaskLog)
            .where(TaskLog.task_id == task_id, TaskLog.log_type == "retry")
        ) or 0
        if retry_count >= settings.max_retry_count:
            raise ValueError(f"超过最大重试次数 {settings.max_retry_count}")
        task = db.get(ApprovalTask, task_id)
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")
        if task.task_status != "blocked":
            raise ValueError("只有 blocked 任务可以重试")
        task.task_status = "parsing"
        db.add(
            TaskLog(
                task_id=task_id,
                log_level="info",
                log_type="retry",
                log_content="人工重试",
            )
        )
        db.commit()
        db.refresh(task)
    write_task_log(task_id, "info", "task", "任务重试已触发")
    return task


def trigger_pull():
    """人工触发入口：拉取待办并入队。"""
    from app.workers.queue import enqueue_task

    tasks = ingest_pending_approvals()
    for task in tasks:
        enqueue_task(task.id)
    return tasks
