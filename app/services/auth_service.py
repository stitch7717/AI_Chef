"""
认证业务逻辑（app/services/auth_service.py）

Service ≈ Java 的 @Service 层：业务规则在这里，可以被多个 Router 复用。
"""

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.auth import Token, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

# bcrypt 是 CPU 密集型同步操作（单次约 200-400ms），直接在 async 函数里调用
# 会阻塞事件循环（并发注册时全部串行排队）。放到线程池执行，事件循环不被阻塞。
import asyncio


async def register(db: AsyncSession, data: UserCreate) -> User:
    """注册：用户名查重 → 密码哈希(线程池) → 入库。"""
    if await user_repo.get_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="用户名已被占用")
    pwd_hash = await asyncio.to_thread(hash_password, data.password)
    user = await user_repo.create(
        db,
        username=data.username,
        password_hash=pwd_hash,
        nickname=data.nickname or data.username,
    )
    return user


async def login(db: AsyncSession, username: str, password: str) -> Token:
    """登录：验证密码(线程池) → 签发 JWT。失败时统一报 401（不透露是账号错还是密码错，防枚举）。"""
    user = await user_repo.get_by_username(db, username)
    ok = user is not None and await asyncio.to_thread(
        verify_password, password, user.password_hash
    )
    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return Token(access_token=create_access_token(user.id))
