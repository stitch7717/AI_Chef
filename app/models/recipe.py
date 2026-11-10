"""
菜谱 / 收藏 / 反馈模型（app/models/recipe.py）

- Recipe.embedding 用 pgvector 的 Vector(512)：
  对应本地向量模型 BAAI/bge-small-zh-v1.5 的输出维度。
  建一次索引全 worker 共享——这是相对 demo 的核心升级之一。
- Feedback 记录"用户做过了、评分如何"，长期看可反哺推荐排序。
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.base import Base, IdMixin, TimestampMixin


class Recipe(Base, IdMixin, TimestampMixin):
    __tablename__ = "recipes"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    ingredients: Mapped[str] = mapped_column(Text)      # JSON 数组：["番茄","鸡蛋"]
    difficulty: Mapped[str] = mapped_column(String(20)) # 简单/中等/困难
    nutrition: Mapped[str] = mapped_column(Text)
    steps: Mapped[str] = mapped_column(Text)
    score_nutrition: Mapped[int | None] = mapped_column(Integer)   # 营养评分 0-10
    score_ease: Mapped[int | None] = mapped_column(Integer)        # 易做评分 0-10
    embedding: Mapped[list[float] | None] = mapped_column(Vector(512))  # 语义向量
    image_url: Mapped[str | None] = mapped_column(String(500))     # 菜品照片（Wikimedia 等）


class Favorite(Base, IdMixin, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe"),)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("recipes.id", ondelete="CASCADE")
    )


class Feedback(Base, IdMixin, TimestampMixin):
    __tablename__ = "feedbacks"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("recipes.id", ondelete="CASCADE")
    )
    rating: Mapped[float] = mapped_column(Float)          # 1-5 分
    cooked: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否真的做过
    comment: Mapped[str | None] = mapped_column(Text)
