"""
会话与消息模型（app/models/chat.py）

对标 LangGraph 的 thread 概念：
- Session  = 一个 thread_id（LangGraph PostgresSaver 的检查点按它隔离）
- Message  = 消息镜像表。LangGraph 的检查点是给模型恢复上下文用的（内部格式复杂），
  业务侧展示历史消息、做统计分析需要一份"人能读"的记录，所以双写。
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin


class ChatSession(Base, IdMixin):
    __tablename__ = "sessions"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(100), default="新对话")   # 取首轮提问截断做标题
    langgraph_thread_id: Mapped[str] = mapped_column(String(64), unique=True)  # 关联 LangGraph 检查点
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Message(Base, IdMixin):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_session_created", "session_id", "id"),)

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    # role: user / assistant
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))   # user 消息附带的图片
