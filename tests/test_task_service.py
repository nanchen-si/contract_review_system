"""任务服务单元测试。"""

import json

import pytest

from app.models.approval import ApprovalTask
from app.models.log import TaskLog
from app.services.task_service import (
    ingest_pending_approvals,
    list_tasks,
    retry_task,
)


@pytest.fixture()
def mock_adapter(monkeypatch, tmp_path):
    """用临时 mock 数据替换真实适配器。"""
    from app.adapters.mock_client import MockClient
    from app.services import task_service

    data_dir = tmp_path / "mock"
    attachments = data_dir / "attachments"
    attachments.mkdir(parents=True)
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
                            {"attachment_id": "ATT-1", "file_name": "合同.docx", "file_type": "docx"}
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        task_service,
        "get_adapter",
        lambda: MockClient(str(data_dir), str(tmp_path / "uploads")),
    )


def test_deduplicate_by_approval_code(db_session, mock_adapter):
    """重复拉取不新建任务。"""
    first = ingest_pending_approvals()
    second = ingest_pending_approvals()
    assert len(first) == 1
    assert first[0].id == second[0].id
    assert list_tasks(task_status="pending", size=10).total == 1


def test_retry_blocked_task(db_session):
    """blocked 重试回到 parsing。"""
    from app.db import get_session

    with next(get_session()) as db:
        task = ApprovalTask(
            approval_code="HT-2",
            approval_title="t",
            applicant_name="a",
            task_status="blocked",
            write_status="not_written",
            create_user_id=1,
        )
        db.add(task)
        db.commit()
        task_id = task.id
    retried = retry_task(task_id)
    assert retried.task_status == "parsing"


def test_retry_exceeds_limit(db_session):
    """超过最大重试次数拒绝重试。"""
    from app.db import get_session

    with next(get_session()) as db:
        task = ApprovalTask(
            approval_code="HT-3",
            approval_title="t",
            applicant_name="a",
            task_status="blocked",
            write_status="not_written",
            create_user_id=1,
        )
        db.add(task)
        db.commit()
        task_id = task.id
        for _ in range(3):
            db.add(TaskLog(task_id=task_id, log_level="info", log_type="retry", log_content="重试"))
        db.commit()
    with pytest.raises(ValueError):
        retry_task(task_id)
