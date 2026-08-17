"""主流程图节点。"""

from sqlalchemy import select

from app.adapters.factory import get_adapter
from app.db import get_session
from app.models.approval import ApprovalAttachment, ApprovalTask
from app.models.result import ReviewResult
from app.services.log_service import write_task_log
from app.tools.approval_tools import download_contract_attachment
from app.tools.document_tools import parse_contract_document
from app.tools.result_tools import write_approval_comment
from app.tools.review_tools import run_contract_rules


def ingest_node(state):
    """拉取审批详情并置任务 parsing。"""
    task_id = state["task_id"]
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")
        approval_code = task.approval_code
        task.task_status = "parsing"
        db.commit()
    detail = get_adapter().get_detail_by_code(approval_code)
    write_task_log(task_id, "info", "task", "进入解析阶段")
    return {"approval_detail": detail, "instance_id": detail.instance_id, "stage": "parsing"}


def download_node(state):
    """下载全部附件并保存附件记录。"""
    detail = state["approval_detail"]
    task_id = state["task_id"]
    paths = []
    for attachment in detail.attachments:
        path = download_contract_attachment(
            detail.instance_id,
            attachment.attachment_id,
            attachment.file_name,
            task_id=task_id,
        )
        paths.append(path)
    write_task_log(task_id, "info", "task", f"下载附件 {len(paths)} 个")
    return {"attachment_path": paths[0] if paths else None, "stage": "parsing"}


def parse_node(state):
    """文本提取/OCR + LLM 字段抽取。"""
    task_id = state["task_id"]
    with next(get_session()) as db:
        attachment = db.scalar(
            select(ApprovalAttachment)
            .where(ApprovalAttachment.task_id == task_id)
            .order_by(ApprovalAttachment.id)
        )
        if attachment is None:
            raise ValueError("无附件可解析")
        attachment_id = attachment.id
    payload = parse_contract_document(attachment_id)
    if payload["parse_status"] != "success":
        raise ValueError(payload.get("parse_error") or "解析失败")
    write_task_log(task_id, "info", "task", "合同解析完成")
    return {"parse_result": payload, "stage": "parsing"}


def review_node(state):
    """执行规则审查流水线。"""
    task_id = state["task_id"]
    result = run_contract_rules(task_id)
    write_task_log(task_id, "info", "task", "规则审查完成")
    return {"review_result": result, "hits": result["hits"], "stage": "reviewing"}


def save_node(state):
    """保存审查结果（流水线已落库，此处同步任务状态）。"""
    task_id = state["task_id"]
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        if task is not None:
            task.task_status = "reviewing"
            db.commit()
    return {"stage": "reviewing"}


def writeback_node(state):
    """生成评论并回写审批系统。"""
    task_id = state["task_id"]
    instance_id = state["instance_id"]
    with next(get_session()) as db:
        review = db.scalar(select(ReviewResult).where(ReviewResult.task_id == task_id))
        if review is None:
            raise ValueError("无审查结果可回写")
        review_id = review.id
    comment = write_approval_comment(instance_id, review_id)
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        if task is not None:
            task.task_status = "done"
            db.commit()
    write_task_log(task_id, "info", "task", "评论回写完成")
    return {"comment_text": comment, "stage": "done"}


def block_node(state):
    """记录异常并置 task_status=blocked。"""
    task_id = state.get("task_id")
    error = state.get("error") or "未知异常"
    with next(get_session()) as db:
        task = db.get(ApprovalTask, task_id)
        if task is not None:
            task.task_status = "blocked"
            db.commit()
    write_task_log(task_id, "error", "task", f"工作流异常：{error}")
    return {"stage": "blocked", "error": error}
