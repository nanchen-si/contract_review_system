"""对外接口冒烟测试。"""

import json

from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.db import get_session
from app.models.approval import ApprovalTask
from app.models.user import User
from app.services import task_service


def _login(client, username: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return r.json()["data"]["token"]


def _admin_headers(client) -> dict:
    settings = get_settings()
    token = _login(client, settings.admin_username, settings.admin_password)
    return {"Authorization": f"Bearer {token}"}


def _seed_admin(db_session):
    settings = get_settings()
    with next(get_session()) as db:
        exists = db.scalar(
            select(User).where(User.username == settings.admin_username)
        )
        if exists is None:
            db.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                )
            )
            db.commit()


def test_health(client):
    """健康检查。"""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_tasks_empty(client):
    """任务列表为空。"""
    r = client.get("/api/tasks")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0


def test_trigger_pull_flow(client, monkeypatch, tmp_path):
    """注册登录后触发拉取，任务入库。"""
    from app.adapters.mock_client import MockClient

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
    client.post("/api/auth/register", json={"username": "u1", "password": "123456"})
    headers = {"Authorization": f"Bearer {_login(client, 'u1', '123456')}"}
    r = client.post("/api/tasks/trigger", headers=headers)
    assert r.status_code == 200
    assert client.get("/api/tasks").json()["data"]["total"] == 1


def test_admin_retry(client, db_session):
    """admin 重试 blocked 任务。"""
    _seed_admin(db_session)
    with next(get_session()) as db:
        task = ApprovalTask(
            approval_code="HT-R",
            approval_title="t",
            applicant_name="a",
            task_status="blocked",
            write_status="not_written",
            create_user_id=1,
        )
        db.add(task)
        db.commit()
        task_id = task.id
    r = client.post(f"/api/tasks/{task_id}/retry", headers=_admin_headers(client))
    assert r.status_code == 200
    assert r.json()["data"]["task_status"] == "parsing"


def test_rules_crud(client, db_session):
    """规则增删改查与逻辑删除。"""
    _seed_admin(db_session)
    headers = _admin_headers(client)
    payload = {
        "rule_code": "RULE_TEST",
        "rule_name": "测试规则",
        "risk_level": "high",
        "rule_status": "enabled",
        "match_mode": "regex",
        "match_text": "测试",
        "suggestion_text": "建议",
    }
    r = client.post("/api/rules", json=payload, headers=headers)
    assert r.status_code == 200
    rule_id = r.json()["data"]["id"]
    assert client.get("/api/rules").json()["data"][0]["rule_code"] == "RULE_TEST"
    r = client.delete(f"/api/rules/{rule_id}", headers=headers)
    assert r.status_code == 200
    assert client.get("/api/rules").json()["data"] == []
