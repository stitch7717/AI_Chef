"""
对话路由（app/api/v1/chat.py）—— Agent 的 HTTP 门面

- POST /chat/{session_id}/stream ：SSE 流式对话（打字机效果），JWT 保护
- POST /chat/{session_id}/invoke ：一次性返回完整回复（测试/调试用）

会话机制：
- LangGraph 记忆按 session.langgraph_thread_id 隔离（PostgresSaver 持久化）
- 每轮对话把 user/assistant 消息镜像写入 messages 表（业务侧可读历史）
- 会话首轮提问自动更新标题与 last_active_at
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.models.chat import ChatSession, Message
from app.models.user import User
from app.repositories import chat as chat_repo
from app.schemas.chat_extra import ChatStreamIn

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/chat", tags=["AI 对话"])


def build_content(message: str, image_url: str | None):
    """组装多模态消息：带图时 deepseek-flash 接受 OpenAI 风格的 image_url。"""
    if image_url:
        return [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    return message


async def get_owned_session(
    session_id: int, user: User, db: AsyncSession
) -> ChatSession:
    session = await chat_repo.get_owned(db, session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return session


async def _stream_agent_events(agent, session: ChatSession, message: str, image_url: str | None):
    """从 Agent 的事件流里提取正文 token，逐段吐出。"""
    from langchain_core.messages import ToolMessage

    inputs = {"messages": [("user", build_content(message, image_url))]}
    config = {"configurable": {"thread_id": session.langgraph_thread_id}}
    async for chunk, _meta in agent.astream(inputs, config, stream_mode="messages"):
        # 排除工具消息：ToolMessage 的 content 是工具原始 JSON（Tavily/RAG），绝不能当正文透传
        if isinstance(chunk, ToolMessage) or getattr(chunk, "type", "") == "tool":
            continue
        text = getattr(chunk, "content", None)
        if not text:
            continue
        if isinstance(text, str):
            yield text
        elif isinstance(text, list):
            # 部分模型把正文放 [{"type":"text","text":...}] 里
            for part in text:
                if isinstance(part, dict) and part.get("type") == "text":
                    yield part.get("text", "")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{session_id}/stream")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,   # slowapi 要求 request 是第一个位置参数
    session_id: int,
    data: ChatStreamIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式对话：token 逐段推送，结束发 done 事件（含落库的消息 id）。"""
    from app.main import get_state   # 延迟导入避免循环依赖

    session = await get_owned_session(session_id, user, db)
    agent = get_state("agent")

    # 首轮提问 → 用提问内容做会话标题
    if session.title == "新对话" and data.message:
        session.title = data.message[:50]
    session.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    async def event_stream():
        full_reply = []
        try:
            yield _sse("start", {"session_id": session.id, "thread": session.langgraph_thread_id})
            async for token in _stream_agent_events(agent, session, data.message, data.image_url):
                full_reply.append(token)
                yield _sse("token", {"text": token})
            reply_text = "".join(full_reply)
            # 双写镜像：用户消息 + 助手回复
            user_msg = await chat_repo.add_message(
                db, session.id, "user", data.message, data.image_url
            )
            assistant_msg = await chat_repo.add_message(db, session.id, "assistant", reply_text)
            yield _sse("done", {
                "user_message_id": user_msg.id,
                "assistant_message_id": assistant_msg.id,
            })
        except Exception as e:   # 模型超时/密钥错误等，给前端一个可读的终止事件
            yield _sse("error", {"detail": f"对话生成失败：{type(e).__name__}: {e}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{session_id}/invoke")
async def chat_invoke(
    session_id: int,
    data: ChatStreamIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """非流式对话：一次性返回完整回复（自动测试与调试用）。"""
    from app.main import get_state

    session = await get_owned_session(session_id, user, db)
    agent = get_state("agent")

    if session.title == "新对话" and data.message:
        session.title = data.message[:50]
    session.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    inputs = {"messages": [("user", build_content(data.message, data.image_url))]}
    config = {"configurable": {"thread_id": session.langgraph_thread_id}}
    result = await agent.ainvoke(inputs, config)
    reply_text = result["messages"][-1].content
    if isinstance(reply_text, list):
        reply_text = "".join(p.get("text", "") for p in reply_text if isinstance(p, dict))

    user_msg = await chat_repo.add_message(db, session.id, "user", data.message, data.image_url)
    assistant_msg = await chat_repo.add_message(db, session.id, "assistant", reply_text)
    return {
        "reply": reply_text,
        "session_id": session.id,
        "user_message_id": user_msg.id,
        "assistant_message_id": assistant_msg.id,
    }
