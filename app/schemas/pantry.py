"""食材库存的数据契约。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# 只允许能精确计量的单位：个/条/片 可按平均重量折算，其余直接换算
ALLOWED_UNITS = ("个", "g", "kg", "斤", "毫升", "条", "片")


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="食材名，如：番茄")
    quantity: float | None = Field(default=None, gt=0, description="数量")
    unit: str | None = Field(default=None, max_length=10, description="单位：个/g/kg/斤/毫升/条/片")
    note: str | None = Field(default=None, description="备注")
    source_image_url: str | None = Field(default=None, max_length=500, description="来源照片")


    @field_validator("unit")
    @classmethod
    def check_unit(cls, v: str | None) -> str | None:
        """单位必须落在白名单内——它是"个→克"折算的依据，脏单位会让估算失真。"""
        if v is None or v == "":
            return None
        if v not in ALLOWED_UNITS:
            raise ValueError(f"单位只支持：{'/'.join(ALLOWED_UNITS)}")
        return v


class PantryItemUpdate(BaseModel):
    """部分更新：只传想改的字段（PATCH 语义）。"""

    quantity: float | None = None
    unit: str | None = None
    note: str | None = None
    consumed: bool | None = None

    @field_validator("unit")
    @classmethod
    def check_unit(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if v not in ALLOWED_UNITS:
            raise ValueError(f"单位只支持：{'/'.join(ALLOWED_UNITS)}")
        return v


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
