"""食材库存的数据契约。"""

from datetime import datetime

from pydantic import BaseModel, Field


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="食材名，如：番茄")
    quantity: float | None = Field(default=None, gt=0, description="数量")
    unit: str | None = Field(default=None, max_length=20, description="单位：个/斤/盒")
    note: str | None = Field(default=None, description="备注")
    source_image_url: str | None = Field(default=None, max_length=500, description="来源照片")


class PantryItemUpdate(BaseModel):
    """部分更新：只传想改的字段（PATCH 语义）。"""

    quantity: float | None = None
    unit: str | None = None
    note: str | None = None
    consumed: bool | None = None


class PantryItemOut(BaseModel):
    id: int
    name: str
    quantity: float | None
    unit: str | None
    note: str | None
    source_image_url: str | None
    consumed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
