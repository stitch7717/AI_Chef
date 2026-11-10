"""收藏路由（app/api/v1/favorites.py）。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.repositories import recipe as recipe_repo
from app.schemas.recipe import FavoriteOut, RecipeOut

router = APIRouter(prefix="/favorites", tags=["收藏"])


@router.get("", response_model=list[RecipeOut])
async def my_favorites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """我的收藏列表（直接返回菜谱详情，前端少一次关联查询）"""
    favs = await recipe_repo.list_favorites(db, user.id)
    result = []
    for fav in favs:
        recipe = await recipe_repo.get_by_id(db, fav.recipe_id)
        if recipe:
            result.append(RecipeOut.model_validate(recipe))
    return result


@router.post("/{recipe_id}", response_model=FavoriteOut, status_code=201)
async def add_favorite(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收藏菜谱（重复收藏幂等：返回已有记录，不报错）"""
    if await recipe_repo.get_by_id(db, recipe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="菜谱不存在")
    existing = await recipe_repo.get_favorite(db, user.id, recipe_id)
    if existing:
        return existing
    return await recipe_repo.add_favorite(db, user.id, recipe_id)


@router.delete("/{recipe_id}", status_code=204)
async def remove_favorite(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏（未收藏时也返回 204，幂等）"""
    fav = await recipe_repo.get_favorite(db, user.id, recipe_id)
    if fav:
        await recipe_repo.remove_favorite(db, fav)
