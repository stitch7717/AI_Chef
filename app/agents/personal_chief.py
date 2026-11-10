"""
私厨 Agent 装配（app/agents/personal_chief.py）

相对 demo 的核心升级：
1. 记忆从 SQLite 文件 → PostgreSQL（AsyncPostgresSaver）：
   多 worker 共享、重启不丢、按 thread_id 隔离会话
2. 模型 deepseek-flash（原生识图）+ Tavily 联网 + pgvector 本地菜谱三件套
3. Agent 是异步构建的（checkpointer 需要异步 setup），由 main.py 的 lifespan
   启动时创建一次，放在 app.state 里
"""

import os

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent
from psycopg_pool import AsyncConnectionPool

from app.agents.recipe_rag import search_local_recipes
from app.core.config import settings

SYSTEM_PROMPT = (
    "你是'AI私厨'，一位专业又贴心的私人厨师助手。"
    "回答遵循以下规则：\n"
    "1. 用户问做什么菜时，优先调用 search_local_recipes 查本地菜谱库；"
    "本地未命中时再用联网搜索查权威做法，并注明来源\n"
    "2. 推荐菜谱时给出：菜名、所需食材、难度、简明步骤、营养亮点\n"
    "3. 用户上传了食材照片时，先描述你识别到的食材，再基于食材推荐\n"
    "4. 语气友好自然，中文回答，不要过度冗长"
)

_pool: AsyncConnectionPool | None = None


def checkpoint_conninfo() -> str:
    """把 sqlalchemy 的 postgresql+asyncpg:// 换成 psycopg 认识的 postgresql://。

    注意：localhost 在 Windows 上可能先解析成 IPv6(::1)，而 Docker 端口只绑了
    127.0.0.1，psycopg 连 ::1 会静默失败导致连接池重试卡死——所以强制用 127.0.0.1。
    """
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return url.replace("localhost", "127.0.0.1")


async def build_agent() -> tuple:
    """
    创建检查点存储池 + 装配 Agent，返回 (agent, pool)。
    由 lifespan 调用一次；pool 的生命周期也由 lifespan 管理（关闭时释放）。
    """
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=checkpoint_conninfo(),
        min_size=1,
        max_size=5,
        open=False,
        # langgraph PostgresSaver 的 setup() 里有 CREATE INDEX CONCURRENTLY，
        # 不能跑在事务块内，必须 autocommit；prepare_threshold=0 走简单查询协议
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    await _pool.open()

    checkpointer = AsyncPostgresSaver(_pool)
    await checkpointer.setup()   # 首次运行自动建 checkpoint 相关表（幂等）

    model = ChatOpenAI(
        model="deepseek-flash",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0.7,
        timeout=120,
    )
    web_search = TavilySearch(
        max_results=3, include_images=True,
        tavily_api_key=settings.TAVILY_API_KEY,   # 显式传参：.env 不会自动进环境变量
    )

    agent = create_react_agent(
        model=model,
        tools=[search_local_recipes, web_search],
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return agent, _pool
