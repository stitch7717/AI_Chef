"""会话路由（app/api/v1/sessions.py）。

阶段 1 提供会话与消息镜像的完整 CRUD；
阶段 2 的 Agent 对话接口会复用这里的数据（langgraph_thread_id）。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.repositories import chat as chat_repo
from app.schemas.chat import MessageOut, SessionCreate, SessionOut

router = APIRouter(prefix="/sessions", tags=["会话"])


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """我的会话列表（按最近活跃排序）"""
    return await chat_repo.list_by_user(db, user.id, limit, offset)


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    data: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新建一个对话会话"""
    return await chat_repo.create(db, user.id, data.title)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（连带删除该会话的全部消息，外键 CASCADE）"""
    session = await chat_repo.get_owned(db, session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="会话不存在")
    await chat_repo.delete_messages(db, session_id)
    await chat_repo.delete(db, session)


@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """读取某会话的历史消息（校验归属）"""
    session = await chat_repo.get_owned(db, session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return await chat_repo.list_messages(db, session_id)
