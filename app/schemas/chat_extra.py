"""对话相关的数据契约。"""

from pydantic import BaseModel, Field


class ChatStreamIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000, description="用户输入")
    image_url: str | None = Field(default=None, max_length=500, description="食材图片URL（OSS）")
