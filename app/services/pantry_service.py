"""库存业务逻辑（app/services/pantry_service.py）"""

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pantry import PantryItem
from app.repositories import pantry as pantry_repo
from app.schemas.pantry import PantryItemIn, PantryItemUpdate


async def add_item(db: AsyncSession, user_id: int, data: PantryItemIn) -> PantryItem:
    """新增食材：同名未消耗的合并数量。

    并发安全说明（业务级关键点）：
    旧实现是「先查后改」，高并发下两个请求同时读到"不存在"，各自插入/
    各自基于旧值累加，导致重复行或数量丢失（压测场景H2实测30并发丢23个）。
    现改为单条原子 upsert：依赖 (user_id, name) 部分唯一索引
    （uq_pantry_active_name，仅约束未消耗行），冲突时在数据库端原子累加，
    不存在读-改-写竞态窗口。对标 Java 侧 INSERT ... ON CONFLICT DO UPDATE。
    """
    excluded = pg_insert(PantryItem).excluded
    stmt = (
        pg_insert(PantryItem)
        .values(
            user_id=user_id,
            name=data.name,
            quantity=data.quantity,
            unit=data.unit,
            note=data.note,
            source_image_url=data.source_image_url,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "name"],
            index_where=PantryItem.consumed == False,  # noqa: E712
            set_={
                # 数量：新值带数量则原子累加；否则保持原值
                "quantity": case(
                    (excluded.quantity.is_(None), PantryItem.quantity),
                    else_=func.coalesce(PantryItem.quantity, 0) + excluded.quantity,
                ),
                # 单位/备注/图片来源：新值带才覆盖
                "unit": func.coalesce(excluded.unit, PantryItem.unit),
                "note": func.coalesce(excluded.note, PantryItem.note),
                "source_image_url": func.coalesce(
                    excluded.source_image_url, PantryItem.source_image_url
                ),
            },
        )
        .returning(PantryItem)
    )
    item = (await db.execute(stmt)).scalar_one()
    await db.commit()
    return item


async def update_item(
    db: AsyncSession, item: PantryItem, data: PantryItemUpdate
) -> PantryItem:
    """部分更新：只覆盖请求里明确传了的字段。"""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


def ensure_owned(item: PantryItem | None) -> PantryItem:
    """统一越权/不存在判断（对外都报 404，不暴露资源是否存在给别人）。"""
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="库存项不存在")
    return item
