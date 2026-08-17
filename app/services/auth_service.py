"""注册、登录、用户查询与缓存读写。"""

from sqlalchemy import select

from app.cache import (
    get_token_session,
    get_user_cache,
    invalidate_user_cache,
    put_token_session,
    put_user_cache,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_session
from app.models.user import User


def register_user(username: str, password: str) -> User:
    """注册 reviewer 账号：唯一性校验、密码哈希、写库并缓存。"""
    with next(get_session()) as db:
        exists = db.scalar(
            select(User).where(User.username == username, User.is_deleted == 0)
        )
        if exists is not None:
            raise ValueError("用户名已存在")
        user = User(
            username=username,
            password_hash=hash_password(password),
            role="reviewer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    put_user_cache(user)
    return user


def login_user(username: str, password: str) -> tuple[str, User]:
    """校验密码并签发 token、缓存登录态。"""
    user = get_user_by_username(username)
    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("用户名或密码错误")
    token = create_access_token(user.id, user.role)
    put_token_session(token, user)
    return token, user


def get_user_by_username(username: str) -> User | None:
    """先缓存后库查询用户。"""
    cached = get_user_cache(username)
    if cached is not None:
        return cached
    with next(get_session()) as db:
        user = db.scalar(
            select(User).where(User.username == username, User.is_deleted == 0)
        )
    if user is not None:
        put_user_cache(user)
    return user


def get_user_by_id(user_id: int) -> User | None:
    """按 id 查询用户。"""
    with next(get_session()) as db:
        return db.get(User, user_id)
