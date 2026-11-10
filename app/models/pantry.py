"""
食材库存模型（app/models/pantry.py）

业务闭环的关键表：识图/手动添加的食材都进这里，
Agent 推荐时优先用用户"真实拥有"的食材，而不是每次现拍现问。
"""

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class PantryItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "pantry_items"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50), index=True)          # 食材名：番茄
    quantity: Mapped[float | None] = mapped_column(Float)              # 数量（可空）
    unit: Mapped[str | None] = mapped_column(String(20))               # 单位：个/斤/盒
    source_image_url: Mapped[str | None] = mapped_column(String(500))  # 来源照片（识图入库时记录）
    confidence: Mapped[float | None] = mapped_column(Float)            # 模型识别置信度 0~1
    note: Mapped[str | None] = mapped_column(Text)                     # 备注：模型对新鲜度的评估等
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 是否已消耗

    # 并发安全关键：同一用户同名未消耗食材只允许一行（库存合并 upsert 依赖此索引）
    __table_args__ = (
        Index(
            "uq_pantry_active_name", "user_id", "name",
            unique=True, postgresql_where=(consumed == False),  # noqa: E712
        ),
    )
