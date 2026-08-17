"""统一日志输出（文件 + 控制台）。"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import get_settings


def setup_logging() -> logging.Logger:
    """初始化 logger，输出到 LOG_DIR 与控制台。"""
    settings = get_settings()
    logger = logging.getLogger("contract_review")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(
        Path(settings.log_dir) / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    """返回命名 logger。"""
    return setup_logging().getChild(name)
