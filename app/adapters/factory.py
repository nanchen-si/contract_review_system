"""按配置选择审批适配器实现。"""

from app.adapters.base import ApprovalAdapter
from app.adapters.mock_client import MockClient
from app.config import get_settings


def get_adapter() -> ApprovalAdapter:
    """按 APPROVAL_ADAPTER 返回适配器实例。"""
    settings = get_settings()
    if settings.approval_adapter == "mock":
        return MockClient(settings.mock_data_dir, settings.upload_dir)
    if settings.approval_adapter == "real":
        raise NotImplementedError("RealClient 尚未实现")
    raise ValueError(f"未知审批适配器: {settings.approval_adapter}")
