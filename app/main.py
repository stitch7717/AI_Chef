"""
应用入口（app/main.py）

对标 Spring Boot 主类 + @Configuration：
- lifespan ≈ @PostConstruct/@PreDestroy：启动时装配 Agent、预热向量模型，
  关闭时释放数据库连接池
- 所有 Router 在这里统一挂载
- slowapi 限流：429 Too Many Requests 的全局异常兜底
"""

import asyncio
import sys

# Windows 下 psycopg(异步) 与 asyncpg 需要 Selector 事件循环；
# 必须在任何事件循环被创建之前设置策略
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.auth import limiter
from app.api.v1 import auth, chat, favorites, feedbacks, oss, pantry, recipes, sessions
from app.core.config import settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    """启动/关闭钩子（对标 @PostConstruct + @PreDestroy）。"""
    # ---- 启动：装配重资源 ----
    from app.agents.embedding import embed_text, vector_to_pgstring
    from app.agents.personal_chief import build_agent
    from app.core.db import async_session_factory, engine
    from sqlalchemy import select, text as sa_text

    agent, pool = await build_agent()
    application.state.agent = agent
    application.state.checkpoint_pool = pool

    # 预热向量模型（首次加载约1-2秒，避免首个请求卡顿）
    embed_text("预热")

    # 给还没有向量的菜谱补 embedding（新导入的菜谱在下次启动时自动补齐）
    async with async_session_factory() as db:
        rows = (await db.execute(
            select(_Recipe).where(_Recipe.embedding.is_(None))
        )).scalars().all()
        if rows:
            from app.agents.embedding import embed_texts
            vectors = embed_texts([
                f"{r.name} 食材:{r.ingredients} 营养:{r.nutrition}" for r in rows
            ])
            for row, vec in zip(rows, vectors):
                row.embedding = vec
            await db.commit()
            print(f"[lifespan] 已为 {len(rows)} 道菜谱补齐向量")

    yield

    # ---- 关闭：释放资源 ----
    pool = getattr(application.state, "checkpoint_pool", None)
    if pool:
        await pool.close()
    await engine.dispose()


# 延迟导入 Recipe 模型，避免模块加载顺序问题
from app.models.recipe import Recipe as _Recipe  # noqa: E402


def get_state(key: str):
    """在 Router 里取 lifespan 装配的资源（agent 等）。"""
    from app.main import app
    return getattr(app.state, key)


def create_app() -> FastAPI:
    """应用工厂（对标 Spring 的 ApplicationContext 组装）。"""
    application = FastAPI(
        title="AI 私厨 Pro",
        description="多用户 AI 私厨应用 · 生产级架构",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 限流：注册/登录/对话均有频控，防暴力破解与刷接口
    application.state.limiter = limiter
    application.add_middleware(SlowAPIMiddleware)

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """把 slowapi 的英文限额（如 10 per 1 minute）转成用户能看懂的中文提示。"""
        import re as _re
        raw = str(exc.detail)
        minute = _re.search(r"(\d+)\s+per\s+(\d+)\s+minute", raw)
        second = _re.search(r"(\d+)\s+per\s+(\d+)\s+second", raw)
        if minute:
            msg = f"操作太频繁了，请稍后再试（每 {minute.group(2)} 分钟最多 {minute.group(1)} 次）"
        elif second:
            msg = f"操作太频繁了，请稍后再试（每 {second.group(2)} 秒最多 {second.group(1)} 次）"
        else:
            msg = "操作太频繁了，请稍后再试"
        return JSONResponse(status_code=429, content={"detail": msg})

    # 挂载业务路由（统一前缀 /api/v1，方便以后出 v2）
    for r in (auth.router, sessions.router, pantry.router,
              recipes.router, favorites.router, feedbacks.router, chat.router, oss.router):
        application.include_router(r, prefix="/api/v1")

    return application


app = create_app()


@app.get("/health")
async def health():
    """健康检查：供负载均衡/容器探针调用。"""
    return {
        "status": "ok",
        "app": "lc-course-pro",
        "jwt_set": settings.JWT_SECRET_KEY != "change-me",
        "llm_set": bool(settings.DEEPSEEK_API_KEY),
    }
