"""
认证接口的数据契约（app/schemas/auth.py）

Pydantic 模型 ≈ Java 的 DTO（Data Transfer Object）：
- 请求进来：自动校验（用户名长度、密码强度），不合规直接 422
- 响应出去：UserOut 里没有 password_hash 字段，密码哈希永远不外泄
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="登录名，3-50字符")
    password: str = Field(min_length=6, max_length=72, description="密码，6-72字符")
    nickname: str | None = Field(default=None, max_length=50)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}   # 允许从 ORM 对象直接转换（≈ @Mapper）


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
