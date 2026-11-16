"""
模型故障降级测试（tests/test_fallback_degrade.py）

背景：DeepSeek 余额不足时，原来只发 error 事件，页面一片空白。
现在要求：先发 fallback 事件（本地 RAG 兜底 3 道菜），再发 error（可读原因）。

做法：把 app.state.agent 换成一个一调用就抛 402 的假 Agent（不花 token），
然后用 TestClient 打 SSE 接口，断言事件序列里出现 fallback 且带菜谱。
"""

import sys

import pytest
from fastapi.testclient import TestClient

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app


class _QuotaExceeded(Exception):
    """模拟 DeepSeek 402 余额不足。"""


class _BrokenAgent:
    async def ainvoke(self, inputs, config):
        raise _QuotaExceeded("Error code: 402 - Insufficient Balance")

    def astream(self, inputs, config, stream_mode=None):
        async def gen():
            raise _QuotaExceeded("Error code: 402 - Insufficient Balance")
            yield  # pragma: no cover —— 让 gen 成为异步生成器

        return gen()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        app.state.limiter.enabled = False
        yield c


def _user(client: TestClient):
    import uuid

    name = f"fb_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/auth/register", json={"username": name, "password": "pass123456"})
    token = client.post(
        "/api/v1/auth/login", json={"username": name, "password": "pass123456"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_model_failure_returns_fallback_recipes(client):
    """模型 402 时：先出 fallback（带本地菜谱），再出 error（带可读原因）。"""
    h = _user(client)
    sid = client.post("/api/v1/sessions", json={"title": "降级测试"}, headers=h).json()["id"]

    original = app.state.agent
    app.state.agent = _BrokenAgent()
    try:
        events = []
        with client.stream(
            "POST", f"/api/v1/chat/{sid}/stream",
            json={"message": "番茄炒蛋怎么做", "image_url": None}, headers=h,
        ) as resp:
            assert resp.status_code == 200
            for line in resp.iter_lines():
                if line.startswith("event: "):
                    events.append(line[7:].strip())
    finally:
        app.state.agent = original

    assert "fallback" in events, f"未出现 fallback 事件：{events}"
    assert "error" in events, f"未出现 error 事件：{events}"
    assert events.index("fallback") < events.index("error"), "fallback 应在 error 之前"
