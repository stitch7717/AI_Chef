"""
模型基类（app/models/base.py）
================================

所有 ORM 模型的公共部分：声明式基类 + 两个通用字段。

SQLAlchemy 2.0 的写法（对标 JPA 的实体类）：
    id: Mapped[int] = mapped_column(primary_key=True)
类型注解即列类型，比旧版 Column() 写法可读性强很多。
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的声明式基类。"""


class IdMixin:
    """主键混入：统一用长整型自增 id（对标 MySQL BIGINT AUTO_INCREMENT）。"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class TimestampMixin:
    """时间戳混入：created_at 数据库自动填充，updated_at 更新时自动刷新。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
