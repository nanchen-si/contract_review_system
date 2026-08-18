"""统一读取配置，向全项目提供配置单例。"""

import os
import warnings
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """项目配置模型，字段与 .env.example 一一对应。

    本地开发优先读取项目根目录 .env；容器部署（无 .env 文件）时读取系统环境变量。
    下方默认值仅作兜底；.env 中的同名变量会覆盖默认值。
    Settings 为进程级单例，修改 .env 后需重启服务（开发可用 uvicorn --reload）才生效。
    """

    model_config = ConfigDict(extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    max_llm_chars: int = 6000
    ocr_confidence_threshold: float = 0.6
    max_retry_count: int = 3
    docx_to_pdf: bool = False
    upload_max_mb: int = 50
    max_pdf_pages: int = 200
    heading_score_threshold: int = 60
    heading_max_length: int = 60
    clause_keywords: str = "付款条款,交付条款,验收条款,违约条款,保密条款,数据条款,知识产权条款,争议解决条款"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "contract_review"
    db_charset: str = "utf8mb4"

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me"
    token_expire_minutes: int = 120

    admin_username: str = "admin"
    admin_password: str = "123456"

    approval_adapter: str = "mock"
    mock_data_dir: str = "mock"
    upload_dir: str = "uploads"
    log_dir: str = "logs"

    @property
    def clause_keyword_list(self) -> list[str]:
        """条款关键词逗号分隔转列表，供标题识别与规则复用。"""
        return [item.strip() for item in self.clause_keywords.split(",") if item.strip()]

    @property
    def llm_base_url_v1(self) -> str:
        """OpenAI 兼容地址：缺 /v1 路径时自动补全。"""
        parsed = urlparse(self.llm_base_url)
        if not parsed.path:
            return self.llm_base_url.rstrip("/") + "/v1"
        return self.llm_base_url

    def model_post_init(self, __context) -> None:
        """把相对目录统一解析为项目根目录下的绝对路径。"""
        self.mock_data_dir = str((BASE_DIR / self.mock_data_dir).resolve())
        self.upload_dir = str((BASE_DIR / self.upload_dir).resolve())
        self.log_dir = str((BASE_DIR / self.log_dir).resolve())
        if self.llm_api_key and not self.llm_base_url.startswith(("http://", "https://")):
            warnings.warn(
                "LLM_BASE_URL 必须以 http:// 或 https:// 开头，当前配置会被忽略；"
                "请确认 .env 中密钥放在 LLM_API_KEY、地址放在 LLM_BASE_URL",
                stacklevel=2,
            )


@lru_cache
def get_settings() -> Settings:
    """读取配置并返回单例：有 .env 时以 .env 为准，否则用系统环境变量。"""
    env_file = BASE_DIR / ".env"
    values: dict[str, str] = {}
    if env_file.exists():
        values.update({key.lower(): value for key, value in dotenv_values(env_file).items()})
    else:
        values.update({key.lower(): value for key, value in os.environ.items() if value})
    return Settings(**values)
