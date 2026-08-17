"""认证接口：注册、登录、当前用户。"""

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.core.deps import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserOut])
def register(payload: RegisterRequest):
    """注册 reviewer 账号。"""
    try:
        user = auth_service.register_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(code=0, message="ok", data=UserOut.model_validate(user))


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: LoginRequest):
    """登录并签发 token。"""
    try:
        token, _user = auth_service.login_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    settings = get_settings()
    return ApiResponse(
        code=0,
        message="ok",
        data=TokenResponse(token=token, expires_in=settings.token_expire_minutes),
    )


@router.get("/me", response_model=ApiResponse[UserOut])
def me(current_user=Depends(get_current_user)):
    """返回当前登录用户。"""
    return ApiResponse(code=0, message="ok", data=UserOut.model_validate(current_user))
