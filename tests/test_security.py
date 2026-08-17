"""安全模块单元测试。"""

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    """密码哈希与校验。"""
    hashed = hash_password("123456")
    assert hashed != "123456"
    assert verify_password("123456", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    """token 签发与解析。"""
    token = create_access_token(1, "admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "admin"
