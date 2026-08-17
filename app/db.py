"""SQLAlchemy engine 与 Session 依赖，并初始化数据库表结构。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

_engine = None
_session_local = None


def get_engine():
    """创建 MySQL engine（pool_pre_ping，utf8mb4），进程内复用。"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            (
                f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}?charset={settings.db_charset}"
            ),
            pool_pre_ping=True,
        )
    return _engine


def get_session():
    """FastAPI 依赖，yield Session。"""
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    db = _session_local()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表并写入种子管理员。"""
    from app.core.security import ensure_admin_seed
    from app.models import Base

    Base.metadata.create_all(bind=get_engine())
    ensure_admin_seed()
