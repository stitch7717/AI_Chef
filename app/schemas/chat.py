"""会话与消息的数据契约。"""

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(default="新对话", max_length=100)


class SessionOut(BaseModel):
    id: int
    title: str
    langgraph_thread_id: str
    last_active_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    image_url: str | None

    model_config = {"from_attributes": True}
