"""密码哈希、token 签发/解析与种子管理员。"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """bcrypt 哈希密码。"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码。"""
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    """签发 JWT，sub 存用户 ID，role 存角色。"""
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """解析并校验 JWT，返回 payload。"""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def ensure_admin_seed():
    """无 admin 时创建种子管理员。"""
    from sqlalchemy import select

    from app.db import get_session
    from app.models.user import User

    settings = get_settings()
    with next(get_session()) as db:
        exists = db.scalar(select(User).where(User.username == settings.admin_username))
        if exists is None:
            db.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                )
            )
            db.commit()
