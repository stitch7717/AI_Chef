"""菜谱 / 收藏 / 反馈的数据契约。"""

import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RecipeOut(BaseModel):
    id: int
    name: str
    ingredients: list[str]        # 库里存 JSON 字符串，出口转成数组
    difficulty: str
    nutrition: str
    steps: str
    score_nutrition: int | None
    score_ease: int | None
    image_url: str | None = None

    model_config = {"from_attributes": True}

    @field_validator("ingredients", mode="before")
    @classmethod
    def parse_ingredients(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class FavoriteOut(BaseModel):
    id: int
    recipe_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackIn(BaseModel):
    recipe_id: int
    rating: float = Field(ge=1, le=5, description="评分 1-5")
    cooked: bool = False
    comment: str | None = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    id: int
    recipe_id: int
    rating: float
    cooked: bool
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
