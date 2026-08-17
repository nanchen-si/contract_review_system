"""统一响应与分页结果模型。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应结构。"""

    code: int
    message: str
    data: T | None = None


class PageResult(BaseModel, Generic[T]):
    """分页结果结构。"""

    items: list[T]
    total: int
    page: int
    size: int
