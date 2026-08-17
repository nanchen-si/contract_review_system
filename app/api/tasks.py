"""任务接口：列表、详情、重试、人工拉取。"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, require_admin
from app.schemas.common import ApiResponse, PageResult
from app.schemas.task import TaskDetail, TaskSummary
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/trigger", response_model=ApiResponse[list])
def trigger_pull(_=Depends(get_current_user)):
    """人工触发拉取待办并入队。"""
    tasks = task_service.trigger_pull()
    return ApiResponse(
        code=0,
        message="ok",
        data=[{"id": task.id, "approval_code": task.approval_code} for task in tasks],
    )


@router.get("", response_model=ApiResponse[PageResult[TaskSummary]])
def list_tasks(task_status: str | None = None, page: int = 1, size: int = 20):
    """任务列表（状态筛选 + 分页）。"""
    return ApiResponse(code=0, message="ok", data=task_service.list_tasks(task_status, page, size))


@router.get("/{task_id}", response_model=ApiResponse[TaskDetail])
def get_task(task_id: int):
    """任务详情聚合。"""
    try:
        return ApiResponse(code=0, message="ok", data=task_service.get_task_detail(task_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{task_id}/retry", response_model=ApiResponse[TaskSummary])
def retry_task(task_id: int, _=Depends(require_admin)):
    """blocked 任务重试（admin）。"""
    try:
        return ApiResponse(
            code=0,
            message="ok",
            data=TaskSummary.model_validate(task_service.retry_task(task_id)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
