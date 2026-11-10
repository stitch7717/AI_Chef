"""会话与消息的数据访问层。"""

import uuid

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, Message


async def list_by_user(db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.last_active_at.desc())
        .limit(limit).offset(offset)
    )
    return result.scalars().all()


async def get_owned(db: AsyncSession, session_id: int, user_id: int) -> ChatSession | None:
    """取会话且校验归属——防止越权访问别人的会话。"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: int, title: str) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        title=title,
        langgraph_thread_id=uuid.uuid4().hex,   # 全局唯一，阶段2给 LangGraph 用
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def delete(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.commit()


async def list_messages(db: AsyncSession, session_id: int, limit: int = 200):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.id).limit(limit)
    )
    return result.scalars().all()


async def delete_messages(db: AsyncSession, session_id: int) -> None:
    await db.execute(sa_delete(Message).where(Message.session_id == session_id))
    await db.commit()


async def add_message(
    db: AsyncSession, session_id: int, role: str, content: str, image_url: str | None = None
) -> Message:
    msg = Message(session_id=session_id, role=role, content=content, image_url=image_url)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
