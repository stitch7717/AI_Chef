"""反馈路由（app/api/v1/feedbacks.py）。

记录"做过了、几分、感受如何"——这是推荐系统冷启动之后最重要的数据资产。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.repositories import recipe as recipe_repo
from app.schemas.recipe import FeedbackIn, FeedbackOut

router = APIRouter(prefix="/feedbacks", tags=["反馈"])


@router.get("", response_model=list[FeedbackOut])
async def my_feedbacks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """我的全部反馈记录"""
    return await recipe_repo.list_feedbacks(db, user.id)


@router.post("", response_model=FeedbackOut, status_code=201)
async def add_feedback(
    data: FeedbackIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交反馈：某菜谱做了没有、评分、评论"""
    if await recipe_repo.get_by_id(db, data.recipe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="菜谱不存在")
    return await recipe_repo.add_feedback(
        db, user.id, data.recipe_id, data.rating, data.cooked, data.comment
    )
