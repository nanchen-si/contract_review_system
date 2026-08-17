"""Mock 适配器单元测试。"""

import json
from pathlib import Path

from app.adapters.factory import get_adapter
from app.adapters.mock_client import MockClient


def _setup_mock(tmp_path: Path) -> tuple[Path, Path]:
    """构造 mock 数据目录与附件。"""
    data_dir = tmp_path / "mock"
    upload_dir = tmp_path / "uploads"
    attachments = data_dir / "attachments"
    attachments.mkdir(parents=True)
    (attachments / "合同.docx").write_bytes(b"docx-bytes")
    (attachments / "扫描.png").write_bytes(b"png-bytes")
    (data_dir / "approvals.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "instance_id": "APP-1",
                        "approval_code": "HT-1",
                        "approval_title": "测试合同审批",
                        "applicant_name": "张三",
                        "application_time": "2026-08-17 10:00:00",
                        "attachments": [
                            {"attachment_id": "ATT-1", "file_name": "合同.docx", "file_type": "docx"},
                            {"attachment_id": "ATT-2", "file_name": "扫描.png", "file_type": "png"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return data_dir, upload_dir


def test_mock_list_pending(tmp_path):
    """list_pending 返回合法记录。"""
    data_dir, upload_dir = _setup_mock(tmp_path)
    client = MockClient(str(data_dir), str(upload_dir))
    records = client.list_pending(10)
    assert len(records) == 1
    assert records[0].approval_code == "HT-1"
    assert records[0].attachment_count == 2


def test_mock_get_detail(tmp_path):
    """get_detail 返回审批详情与附件列表。"""
    data_dir, upload_dir = _setup_mock(tmp_path)
    client = MockClient(str(data_dir), str(upload_dir))
    detail = client.get_detail("APP-1")
    assert detail.instance_id == "APP-1"
    assert detail.applicant_name == "张三"
    assert len(detail.attachments) == 2


def test_mock_download(tmp_path):
    """download 复制附件并返回路径与校验值。"""
    data_dir, upload_dir = _setup_mock(tmp_path)
    client = MockClient(str(data_dir), str(upload_dir))
    result = client.download("APP-1", "ATT-1", "合同.docx")
    assert Path(result.file_path).exists()
    assert result.file_checksum


def test_mock_write_comment(tmp_path):
    """write_comment 写 JSON 并返回回写结果。"""
    data_dir, upload_dir = _setup_mock(tmp_path)
    client = MockClient(str(data_dir), str(upload_dir))
    result = client.write_comment("APP-1", 7)
    assert result.success is True
    assert (data_dir / "comments" / "APP-1.json").exists()


def test_factory_returns_mock(monkeypatch, tmp_path):
    """工厂按配置返回 MockClient。"""
    from app.adapters import factory
    from app.config import Settings

    data_dir, upload_dir = _setup_mock(tmp_path)
    settings = Settings(
        approval_adapter="mock",
        mock_data_dir=str(data_dir),
        upload_dir=str(upload_dir),
    )
    monkeypatch.setattr(factory, "get_settings", lambda: settings)
    adapter = get_adapter()
    assert isinstance(adapter, MockClient)
