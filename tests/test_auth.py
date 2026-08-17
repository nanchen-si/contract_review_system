"""认证服务与接口测试。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router as auth_router


def make_client() -> TestClient:
    """用最小 FastAPI 应用挂载认证路由。"""
    app = FastAPI()
    app.include_router(auth_router)
    return TestClient(app)


def test_register_and_login(db_session):
    """注册后登录成功并拿到 token。"""
    client = make_client()
    r = client.post("/api/auth/register", json={"username": "reviewer1", "password": "123456"})
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "reviewer"

    r2 = client.post("/api/auth/login", json={"username": "reviewer1", "password": "123456"})
    assert r2.status_code == 200
    assert r2.json()["data"]["token"]


def test_duplicate_register(db_session):
    """重复注册返回 400。"""
    client = make_client()
    payload = {"username": "dup", "password": "123456"}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400


def test_login_wrong_password(db_session):
    """密码错误返回 401。"""
    client = make_client()
    client.post("/api/auth/register", json={"username": "u2", "password": "123456"})
    r = client.post("/api/auth/login", json={"username": "u2", "password": "wrong"})
    assert r.status_code == 401


def test_me_with_token(db_session):
    """带 token 访问 /me 成功。"""
    client = make_client()
    client.post("/api/auth/register", json={"username": "u3", "password": "123456"})
    login = client.post("/api/auth/login", json={"username": "u3", "password": "123456"})
    token = login.json()["data"]["token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "u3"
