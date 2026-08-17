"""pytest 共享夹具：用 SQLite 内存库替换 MySQL，保证测试隔离。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db
from app.models import Base


@pytest.fixture()
def db_session(monkeypatch):
    """每个测试独立的内存 SQLite 库。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(app.db, "_engine", engine)
    monkeypatch.setattr(
        app.db,
        "_session_local",
        sessionmaker(bind=engine, autoflush=False, autocommit=False),
    )
    yield engine
    engine.dispose()
