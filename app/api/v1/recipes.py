"""菜谱路由（app/api/v1/recipes.py）。

阶段 1 提供查询能力；菜谱数据的写入走 scripts/seed_recipes.py（离线导入）。
阶段 2 会在 recipes 表上补 embedding 并新增 /search/similar 语义检索接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.repositories import recipe as recipe_repo
from app.schemas.recipe import RecipeOut

router = APIRouter(prefix="/recipes", tags=["菜谱"])


@router.get("", response_model=list[RecipeOut])
async def list_recipes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="每页数量（上限 200）"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """菜谱列表（分页）"""
    return await recipe_repo.list_recipes(db, limit, offset)


@router.get("/search", response_model=list[RecipeOut])
async def search_recipes(
    keyword: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按菜名关键字搜索（模糊匹配）"""
    return await recipe_repo.search_by_name(db, keyword)


@router.get("/{recipe_id}", response_model=RecipeOut)
async def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """菜谱详情"""
    recipe = await recipe_repo.get_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="菜谱不存在")
    return recipe
