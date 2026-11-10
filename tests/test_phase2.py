"""
阶段 2 自动化测试（tests/test_phase2.py）

运行方式：
    uv run pytest tests/test_phase2.py -v

设计：
- lifespan 会真实装配 Agent（PostgresSaver 建检查点表、fastembed 预热、菜谱向量补齐）；
- 对话模型用 FakeAgent 替身（不耗 token、可离线重复），但记忆隔离、消息镜像、
  SSE 事件协议、pgvector 检索全部走真实代码路径。
"""

import sys
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        app.state.limiter.enabled = False
        yield c


@pytest.fixture()
def fake_agent():
    """替身 Agent：记录每次调用的 thread_id，便于验证记忆连续性。"""
    calls = []

    class FakeChunk:
        def __init__(self, text):
            self.content = text

    class FakeAgent:
        async def ainvoke(self, inputs, config):
            thread = config["configurable"]["thread_id"]
            calls.append(thread)
            return {"messages": [SimpleNamespace(content=f"假模型回复[{thread[:8]}]")]}

        def astream(self, inputs, config, stream_mode=None):
            async def gen():
                thread = config["configurable"]["thread_id"]
                calls.append(thread)
                for piece in ["假", "模", "型", "流", "式", f"[{thread[:8]}]"]:
                    yield FakeChunk(piece), {}
            return gen()

    fake = FakeAgent()
    fake.calls = calls
    original = app.state.agent
    app.state.agent = fake
    yield fake
    app.state.agent = original


def register_and_login(client, prefix="p2"):
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/auth/register", json={"username": username, "password": "pass123456"})
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "pass123456"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def new_session(client, headers, title="测试会话"):
    return client.post("/api/v1/sessions", json={"title": title}, headers=headers).json()["id"]


# ==================== 权限 ====================

def test_chat_requires_auth(client):
    r = client.post("/api/v1/chat/1/invoke", json={"message": "hi"})
    assert r.status_code == 401


def test_chat_404_for_others_session(client):
    """用户B不能对用户A的会话发起对话。"""
    h_a = register_and_login(client, "chatA")
    h_b = register_and_login(client, "chatB")
    sid = new_session(client, h_a)
    r = client.post(f"/api/v1/chat/{sid}/invoke", json={"message": "hi"}, headers=h_b)
    assert r.status_code == 404


# ==================== 对话与镜像 ====================

def test_invoke_writes_message_mirror(client, fake_agent):
    h = register_and_login(client, "chatI")
    sid = new_session(client, h, "我的私厨")
    before = len(client.get(f"/api/v1/sessions/{sid}/messages", headers=h).json())

    r = client.post(f"/api/v1/chat/{sid}/invoke", json={"message": "番茄鸡蛋怎么炒"}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"].startswith("假模型回复")

    # 消息镜像：user + assistant 两条都落库
    msgs = client.get(f"/api/v1/sessions/{sid}/messages", headers=h).json()
    assert len(msgs) == before + 2
    assert msgs[-2]["role"] == "user" and msgs[-2]["content"] == "番茄鸡蛋怎么炒"
    assert msgs[-1]["role"] == "assistant"


def test_invoke_updates_session_title(client, fake_agent):
    h = register_and_login(client, "chatT")
    sid = new_session(client, h, "新对话")
    client.post(f"/api/v1/chat/{sid}/invoke", json={"message": "今晚吃红烧肉还是清蒸鱼"}, headers=h)
    sessions = client.get("/api/v1/sessions", headers=h).json()
    target = next(s for s in sessions if s["id"] == sid)
    assert target["title"] == "今晚吃红烧肉还是清蒸鱼"


def test_memory_thread_continuity(client, fake_agent):
    """同一会话多次对话复用同一 thread_id；不同会话 thread_id 不同（Agent 记忆隔离的根基）。"""
    h = register_and_login(client, "chatM")
    sid1 = new_session(client, h)
    sid2 = new_session(client, h)
    client.post(f"/api/v1/chat/{sid1}/invoke", json={"message": "一"}, headers=h)
    client.post(f"/api/v1/chat/{sid1}/invoke", json={"message": "二"}, headers=h)
    client.post(f"/api/v1/chat/{sid2}/invoke", json={"message": "三"}, headers=h)
    assert fake_agent.calls[0] == fake_agent.calls[1]      # 同会话同 thread
    assert fake_agent.calls[0] != fake_agent.calls[2]      # 异会话异 thread


def test_stream_sse_protocol(client, fake_agent):
    """SSE 流式：start → 多个 token → done，正文完整。"""
    h = register_and_login(client, "chatS")
    sid = new_session(client, h)
    with client.stream(
        "POST", f"/api/v1/chat/{sid}/stream",
        json={"message": "推荐个菜"}, headers=h,
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = []
        for line in resp.iter_lines():
            if line.startswith("data: "):
                events.append(line[6:])
    # 第一条是 start，最后一条是 done
    import json as _json
    assert "session_id" in _json.loads(events[0])
    done = _json.loads(events[-1])
    assert "assistant_message_id" in done
    # 中间 token 拼起来是完整回复
    tokens = "".join(_json.loads(e)["text"] for e in events[1:-1])
    assert tokens.startswith("假模型流式")


# ==================== pgvector 检索（真实路径） ====================

def _fresh_session_factory():
    """测试里 asyncio.run() 会开新事件循环，全局连接池（绑定 TestClient 的循环）
    不能跨循环使用——这里创建独立的会话工厂规避。"""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def test_pgvector_search_hit(monkeypatch):
    """lifespan 已给菜谱补齐向量：'番茄炒蛋' 应高相似命中。"""
    from app.agents import recipe_rag
    import asyncio
    monkeypatch.setattr(recipe_rag, "async_session_factory", _fresh_session_factory())

    results = asyncio.run(recipe_rag.search_recipes_by_vector("西红柿炒鸡蛋", 3))
    assert results, "应有命中结果"
    assert results[0]["name"] == "番茄炒蛋"
    assert results[0]["similarity"] > 0.55


def test_rag_tool_miss_guides_to_web(monkeypatch):
    """无关查询应返回'未命中'提示，引导 Agent 转联网搜索。"""
    from app.agents import recipe_rag
    import asyncio
    monkeypatch.setattr(recipe_rag, "async_session_factory", _fresh_session_factory())

    out = asyncio.run(recipe_rag.search_local_recipes.ainvoke({"query": "量子力学的薛定谔方程"}))
    assert "未命中" in out


def test_recipes_have_embeddings(client):
    """启动后所有菜谱都应有向量（新导入的会被 lifespan 自动补齐）。"""
    import asyncio
    from sqlalchemy import func, select, text
    from app.models.recipe import Recipe

    factory = _fresh_session_factory()

    async def count():
        async with factory() as db:
            total = (await db.execute(select(func.count(Recipe.id)))).scalar()
            with_vec = (await db.execute(
                select(func.count(Recipe.id)).where(Recipe.embedding.is_not(None))
            )).scalar()
            return total, with_vec

    total, with_vec = asyncio.run(count())
    assert total > 0 and total == with_vec
