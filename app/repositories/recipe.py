"""菜谱 / 收藏 / 反馈的数据访问层。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Favorite, Feedback, Recipe


async def list_recipes(db: AsyncSession, limit: int = 50, offset: int = 0):
    result = await db.execute(select(Recipe).order_by(Recipe.id).limit(limit).offset(offset))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, recipe_id: int) -> Recipe | None:
    return await db.get(Recipe, recipe_id)


async def search_by_name(db: AsyncSession, keyword: str, limit: int = 20):
    result = await db.execute(
        select(Recipe).where(Recipe.name.ilike(f"%{keyword}%")).limit(limit)
    )
    return result.scalars().all()


async def count_all(db: AsyncSession) -> int:
    result = await db.execute(select(Recipe.id))
    return len(result.scalars().all())


async def upsert(db: AsyncSession, recipe: Recipe) -> Recipe:
    await db.merge(recipe)   # 按 name 唯一键合并（存在则更新，不存在则插入）
    await db.commit()
    return recipe


async def get_recipe_by_name(db: AsyncSession, name: str) -> Recipe | None:
    result = await db.execute(select(Recipe).where(Recipe.name == name))
    return result.scalar_one_or_none()


# ---- 收藏 ----

async def list_favorites(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
    )
    return result.scalars().all()


async def get_favorite(db: AsyncSession, user_id: int, recipe_id: int) -> Favorite | None:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.recipe_id == recipe_id)
    )
    return result.scalar_one_or_none()


async def add_favorite(db: AsyncSession, user_id: int, recipe_id: int) -> Favorite:
    """收藏（并发幂等）。

    旧实现先查后插，两个并发请求同时读到"未收藏"时都执行 INSERT，
    后提交者触发唯一约束 uq_user_recipe 变成 500（压测场景H1实测2次）。
    现捕获 IntegrityError 后回落为查询已有记录返回——语义等价于幂等收藏。
    """
    fav = Favorite(user_id=user_id, recipe_id=recipe_id)
    db.add(fav)
    try:
        await db.commit()
        await db.refresh(fav)
        return fav
    except IntegrityError:
        await db.rollback()
        existing = await get_favorite(db, user_id, recipe_id)
        assert existing is not None  # 约束冲突说明它必然存在
        return existing


async def remove_favorite(db: AsyncSession, fav: Favorite) -> None:
    await db.delete(fav)
    await db.commit()


# ---- 反馈 ----

async def list_feedbacks(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Feedback).where(Feedback.user_id == user_id).order_by(Feedback.created_at.desc())
    )
    return result.scalars().all()


async def add_feedback(
    db: AsyncSession, user_id: int, recipe_id: int, rating: float,
    cooked: bool, comment: str | None,
) -> Feedback:
    fb = Feedback(
        user_id=user_id, recipe_id=recipe_id,
        rating=rating, cooked=cooked, comment=comment,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return fb
