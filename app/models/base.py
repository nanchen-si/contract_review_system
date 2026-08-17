"""SQLAlchemy 声明式基类。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """统一元数据的声明式基类。"""
