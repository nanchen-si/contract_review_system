"""运行日志查询接口。"""

from fastapi import APIRouter, Depends

from app.core.deps import require_admin
from app.schemas.common import ApiResponse, PageResult
from app.schemas.log import LogOut
from app.services.log_service import list_task_logs

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=ApiResponse[PageResult[LogOut]])
def list_logs(
    task_id: int | None = None,
    log_level: str | None = None,
    log_type: str | None = None,
    page: int = 1,
    size: int = 20,
    _=Depends(require_admin),
):
    """日志列表（admin，按级别/类型/任务筛选）。"""
    result = list_task_logs(task_id, log_level, log_type, page, size)
    items = [LogOut.model_validate(item) for item in result.items]
    return ApiResponse(
        code=0,
        message="ok",
        data=PageResult(items=items, total=result.total, page=result.page, size=result.size),
    )
