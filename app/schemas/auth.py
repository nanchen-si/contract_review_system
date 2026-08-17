"""认证相关请求/响应模型。"""

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str
    password: str


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """登录响应。"""

    token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    """用户信息输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
