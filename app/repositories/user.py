"""
用户数据访问层（app/repositories/user.py）

Repository ≈ Java 的 DAO/Mapper：只负责"增删改查"，不含业务判断。
业务规则（比如"用户名已占用怎么办"）归 Service 层管。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def create(
    db: AsyncSession,
    username: str,
    password_hash: str,
    nickname: str | None,
) -> User:
    user = User(username=username, password_hash=password_hash, nickname=nickname)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
