"""统一读取 .env，向全项目提供配置单例。"""

from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """项目配置模型，字段与 .env.example 一一对应。

    配置只来自项目根目录 .env，不读取系统环境变量。
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

    def model_post_init(self, __context) -> None:
        """把相对目录统一解析为项目根目录下的绝对路径。"""
        self.mock_data_dir = str((BASE_DIR / self.mock_data_dir).resolve())
        self.upload_dir = str((BASE_DIR / self.upload_dir).resolve())
        self.log_dir = str((BASE_DIR / self.log_dir).resolve())


@lru_cache
def get_settings() -> Settings:
    """从项目根 .env 读取配置并返回单例。"""
    values = {key.lower(): value for key, value in dotenv_values(BASE_DIR / ".env").items()}
    return Settings(**values)
