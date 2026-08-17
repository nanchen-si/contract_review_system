"""审批类工具：拉取、详情、下载。"""

from sqlalchemy import select

from app.adapters.factory import get_adapter
from app.db import get_session
from app.models.approval import ApprovalAttachment, ApprovalTask


def list_pending_contract_approvals(limit: int = 20) -> list[ApprovalTask]:
    """拉取待办并去重入库，返回任务列表。"""
    records = get_adapter().list_pending(limit)
    tasks: list[ApprovalTask] = []
    with next(get_session()) as db:
        for record in records:
            existing = db.scalar(
                select(ApprovalTask).where(ApprovalTask.approval_code == record.approval_code)
            )
            if existing is not None:
                tasks.append(existing)
                continue
            task = ApprovalTask(
                approval_code=record.approval_code,
                approval_title=record.approval_title,
                applicant_name=record.applicant_name,
                task_status="pending",
                write_status="not_written",
                create_user_id=1,
            )
            db.add(task)
            db.flush()
            tasks.append(task)
        db.commit()
    return tasks


def get_contract_approval(instance_id: str):
    """返回审批详情（ApprovalDetail）。"""
    return get_adapter().get_detail(instance_id)


def download_contract_attachment(instance_id: str, attachment_id: str, file_name: str, task_id: int | None = None) -> str:
    """下载附件并保存附件记录，返回本地路径。"""
    result = get_adapter().download(instance_id, attachment_id, file_name)
    if task_id is not None:
        with next(get_session()) as db:
            db.execute(
                ApprovalAttachment.__table__.delete().where(
                    ApprovalAttachment.task_id == task_id,
                    ApprovalAttachment.attachment_id == attachment_id,
                )
            )
            db.add(
                ApprovalAttachment(
                    task_id=task_id,
                    attachment_id=attachment_id,
                    file_name=file_name,
                    file_type=file_name.rsplit(".", 1)[-1].lower(),
                    file_path=result.file_path,
                    download_status="downloaded",
                    create_user_id=1,
                )
            )
            db.commit()
    return result.file_path
