"""
Alembic 迁移环境（alembic/env.py）

职责：把 SQLAlchemy 元数据交给 Alembic，让它能对比"模型定义"和"数据库现状"
自动生成迁移脚本（autogenerate）。

【异步说明】
项目用的是 asyncpg 异步驱动，但 Alembic 的迁移执行是同步流程，
所以这里用 DATABASE_URL_SYNC（psycopg 同步驱动）连接——同一个库，两把钥匙。
"""

import asyncio
import sys
from pathlib import Path

from logging.config import fileConfig

# 把项目根目录加入 sys.path，alembic 才能找到 app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models import Base   # 导入全部模型，元数据才能被收集到

config = context.config

# 日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 从 .env 注入同步连接串
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

# autogenerate 的对比基准
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL 不连库（很少用）。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步引擎在线执行迁移（与 db.py 的连接池参数保持一致）。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    # Windows 默认的 ProactorEventLoop 与 psycopg 异步模式不兼容，切换到 Selector
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
