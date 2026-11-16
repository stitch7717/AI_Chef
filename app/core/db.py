"""
数据库连接（app/core/db.py）
================================

对标 Java 的 DataSource + 连接池 + 事务管理器：

- create_async_engine  ≈ Druid/HikariCP 连接池（pool_size 控制并发连接数）
- async_sessionmaker   ≈ SqlSessionFactory / EntityManager 工厂
- get_db()             ≈ @Transactional 的依赖注入版本：
                         FastAPI 通过 Depends(get_db) 给每个请求发一个会话，
                         请求结束自动关闭，异常自动回滚。

【为什么用 async】
FastAPI 的事件循环里，同步数据库调用会阻塞整个 worker；
asyncpg 驱动让数据库等待期间线程可以去处理其他请求——这正是并发能力的关键。
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# 连接池：容量必须与 worker 数联动
#   单实例最大连接 = pool_size + max_overflow
#   多实例/多 worker 时总量 = 实例数 × (pool_size + max_overflow)，要小于 PG 的 max_connections
#   例：4 worker × 30 = 120 > 默认 100 → 会出现"实例越多越连不上"的雪崩
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=True,      # 每次取连接前探活，防止拿到断开的连接
    echo=False,              # True 时打印所有 SQL（调试用）
)

# 会话工厂：expire_on_commit=False 让提交后对象属性仍可读（异步下不能用惰性加载）
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每个请求一个数据库会话，请求结束自动关闭。"""
    async with async_session_factory() as session:
        yield session
