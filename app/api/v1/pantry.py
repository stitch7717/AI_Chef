"""食材库存路由（app/api/v1/pantry.py）。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.repositories import pantry as pantry_repo
from app.schemas.pantry import PantryItemIn, PantryItemOut, PantryItemUpdate
from app.services import pantry_service

router = APIRouter(prefix="/pantry", tags=["食材库存"])


@router.get("", response_model=list[PantryItemOut])
async def list_items(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_consumed: bool = False,
):
    """我的库存列表（默认不含已消耗的）"""
    return await pantry_repo.list_by_user(db, user.id, include_consumed)


@router.post("", response_model=PantryItemOut, status_code=201)
async def add_item(
    data: PantryItemIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加食材（同名未消耗的自动合并数量；阶段2识图后自动调这里）"""
    return await pantry_service.add_item(db, user.id, data)


@router.patch("/{item_id}", response_model=PantryItemOut)
async def update_item(
    item_id: int,
    data: PantryItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改库存项（数量/单位/备注/标记已消耗）"""
    item = pantry_service.ensure_owned(await pantry_repo.get_owned(db, item_id, user.id))
    return await pantry_service.update_item(db, item, data)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除库存项"""
    item = pantry_service.ensure_owned(await pantry_repo.get_owned(db, item_id, user.id))
    await pantry_repo.delete(db, item)
