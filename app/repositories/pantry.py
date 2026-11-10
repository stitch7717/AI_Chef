"""食材库存的数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pantry import PantryItem


async def list_by_user(db: AsyncSession, user_id: int, include_consumed: bool = False):
    stmt = select(PantryItem).where(PantryItem.user_id == user_id)
    if not include_consumed:
        stmt = stmt.where(PantryItem.consumed == False)  # noqa: E712
    stmt = stmt.order_by(PantryItem.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_owned(db: AsyncSession, item_id: int, user_id: int) -> PantryItem | None:
    result = await db.execute(
        select(PantryItem).where(PantryItem.id == item_id, PantryItem.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def find_same_name(db: AsyncSession, user_id: int, name: str) -> PantryItem | None:
    """同名未消耗的食材视为同一条（避免"番茄"重复入库存）。"""
    result = await db.execute(
        select(PantryItem).where(
            PantryItem.user_id == user_id,
            PantryItem.name == name,
            PantryItem.consumed == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: int, **fields) -> PantryItem:
    item = PantryItem(user_id=user_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: PantryItem) -> None:
    await db.delete(item)
    await db.commit()
