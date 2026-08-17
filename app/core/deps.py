"""当前用户与 admin 校验依赖。"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.cache import get_token_session
from app.core.security import decode_access_token
from app.services.auth_service import get_user_by_id

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """从 token 解析当前用户（缓存优先），失败抛 401。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    token = credentials.credentials
    cached = get_token_session(token)
    if cached is not None:
        return cached
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    user = get_user_by_id(int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(current_user=Depends(get_current_user)):
    """校验当前用户为 admin，否则抛 403。"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
