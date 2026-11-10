"""
阶段 1 自动化测试（tests/test_phase1.py）

运行方式：
    uv run pytest tests/test_phase1.py -v

关键设计：
- client 用模块级 fixture + with 上下文：所有请求共享同一个事件循环，
  asyncpg 连接池才不会跨循环报错（这是异步应用测试最常踩的坑）；
- 限流器默认关闭（TestClient 所有请求同一 IP），只在专门的限流用例里临时打开；
- 用户名带随机后缀，测试可重复执行；数据库为真实 PostgreSQL 容器。
"""

import sys
import uuid

import pytest
from fastapi.testclient import TestClient

# Windows 下让 asyncpg 用 Selector 事件循环，避免 Proactor 兼容问题
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # 测试期间关闭限流，避免误伤；限流用例里再单独打开
        app.state.limiter.enabled = False
        yield c


def make_user(client: TestClient, prefix: str = "u"):
    """注册一个随机用户并返回 (用户名, 密码, token)。"""
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    password = "pass123456"
    r = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201, r.text
    r2 = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r2.status_code == 200, r2.text
    return username, password, r2.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ==================== 认证 ====================

def test_register_ok(client):
    username, password, _ = make_user(client, "reg")
    assert username.startswith("reg_")


def test_register_duplicate_409(client):
    username, password, _ = make_user(client, "dup")
    r = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    assert r.status_code == 409


def test_register_password_too_short_422(client):
    r = client.post("/api/v1/auth/register", json={"username": "shortpw_user", "password": "123"})
    assert r.status_code == 422


def test_login_wrong_password_401(client):
    username, password, _ = make_user(client, "wrongpw")
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "definitely-wrong"})
    assert r.status_code == 401


def test_me_with_token(client):
    username, password, token = make_user(client, "me")
    r = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == username
    assert "password_hash" not in body          # 密码哈希绝不能外泄
    assert "password" not in body


def test_me_without_token_401(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_bad_token_401(client):
    r = client.get("/api/v1/auth/me", headers=auth_header("not-a-real-token"))
    assert r.status_code == 401


# ==================== 会话与消息 ====================

def test_session_crud_flow(client):
    _, _, token = make_user(client, "sess")
    # 创建
    r = client.post("/api/v1/sessions", json={"title": "今晚吃什么"}, headers=auth_header(token))
    assert r.status_code == 201
    sid = r.json()["id"]
    assert r.json()["langgraph_thread_id"]      # 阶段2 Agent 要用
    # 列表
    r = client.get("/api/v1/sessions", headers=auth_header(token))
    assert any(s["id"] == sid for s in r.json())
    # 删除后消息应 404
    r = client.delete(f"/api/v1/sessions/{sid}", headers=auth_header(token))
    assert r.status_code == 204
    r = client.get(f"/api/v1/sessions/{sid}/messages", headers=auth_header(token))
    assert r.status_code == 404


def test_session_isolation_between_users(client):
    """会话隔离：用户A的会话，用户B看不到也删不了。"""
    _, _, token_a = make_user(client, "isoA")
    _, _, token_b = make_user(client, "isoB")
    sid = client.post("/api/v1/sessions", json={}, headers=auth_header(token_a)).json()["id"]
    assert client.get(f"/api/v1/sessions/{sid}/messages",
                      headers=auth_header(token_b)).status_code == 404
    assert client.delete(f"/api/v1/sessions/{sid}",
                         headers=auth_header(token_b)).status_code == 404


# ==================== 食材库存 ====================

def test_pantry_add_merge_update_delete(client):
    _, _, token = make_user(client, "pantry")
    h = auth_header(token)
    # 添加
    r = client.post("/api/v1/pantry", json={"name": "番茄", "quantity": 2, "unit": "个"}, headers=h)
    assert r.status_code == 201
    item_id = r.json()["id"]
    # 同名合并：再加 3 个，数量应变成 5
    r = client.post("/api/v1/pantry", json={"name": "番茄", "quantity": 3, "unit": "个"}, headers=h)
    assert r.status_code == 201
    assert r.json()["quantity"] == 5
    # 部分更新：标记已消耗
    r = client.patch(f"/api/v1/pantry/{item_id}", json={"consumed": True}, headers=h)
    assert r.status_code == 200 and r.json()["consumed"] is True
    # 默认列表不含已消耗项
    r = client.get("/api/v1/pantry", headers=h)
    assert all(i["consumed"] is False for i in r.json())
    # 删除
    assert client.delete(f"/api/v1/pantry/{item_id}", headers=h).status_code == 204
    # 再删一次 404
    assert client.delete(f"/api/v1/pantry/{item_id}", headers=h).status_code == 404


def test_pantry_isolation_between_users(client):
    _, _, token_a = make_user(client, "panA")
    _, _, token_b = make_user(client, "panB")
    item_id = client.post("/api/v1/pantry", json={"name": "鸡蛋"},
                          headers=auth_header(token_a)).json()["id"]
    # B 不能改/删 A 的库存项
    assert client.patch(f"/api/v1/pantry/{item_id}", json={"consumed": True},
                        headers=auth_header(token_b)).status_code == 404
    assert client.delete(f"/api/v1/pantry/{item_id}",
                         headers=auth_header(token_b)).status_code == 404


# ==================== 菜谱 ====================

def test_recipes_seeded_and_searchable(client):
    _, _, token = make_user(client, "recipe")
    h = auth_header(token)
    r = client.get("/api/v1/recipes", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 10                       # seed 导入的 10 道
    assert isinstance(r.json()[0]["ingredients"], list)   # JSON 字符串已转数组
    # 关键字搜索
    r = client.get("/api/v1/recipes/search", params={"keyword": "番茄"}, headers=h)
    assert any("番茄" in recipe["name"] for recipe in r.json())
    # 详情 404
    assert client.get("/api/v1/recipes/999999", headers=h).status_code == 404


# ==================== 收藏与反馈 ====================

def test_favorite_flow(client):
    _, _, token = make_user(client, "fav")
    h = auth_header(token)
    recipe_id = client.get("/api/v1/recipes", headers=h).json()[0]["id"]
    # 收藏 → 幂等重复收藏 → 列表里有 → 取消 → 列表为空 → 再取消也 204
    assert client.post(f"/api/v1/favorites/{recipe_id}", headers=h).status_code == 201
    assert client.post(f"/api/v1/favorites/{recipe_id}", headers=h).status_code == 201
    assert len(client.get("/api/v1/favorites", headers=h).json()) == 1
    assert client.delete(f"/api/v1/favorites/{recipe_id}", headers=h).status_code == 204
    assert client.get("/api/v1/favorites", headers=h).json() == []
    assert client.delete(f"/api/v1/favorites/{recipe_id}", headers=h).status_code == 204
    # 收藏不存在的菜谱 → 404
    assert client.post("/api/v1/favorites/999999", headers=h).status_code == 404


def test_feedback_flow(client):
    _, _, token = make_user(client, "fb")
    h = auth_header(token)
    recipe_id = client.get("/api/v1/recipes", headers=h).json()[0]["id"]
    # 正常提交
    r = client.post("/api/v1/feedbacks",
                    json={"recipe_id": recipe_id, "rating": 4.5, "cooked": True, "comment": "好吃"},
                    headers=h)
    assert r.status_code == 201
    # 评分越界 → 422
    r = client.post("/api/v1/feedbacks", json={"recipe_id": recipe_id, "rating": 9}, headers=h)
    assert r.status_code == 422
    # 我的反馈列表
    r = client.get("/api/v1/feedbacks", headers=h)
    assert len(r.json()) == 1 and r.json()[0]["rating"] == 4.5


# ==================== 限流（放最后，临时打开限流器） ====================

def test_rate_limit_429(client):
    """连续注册超过 10 次/分钟应触发 429。"""
    app.state.limiter.enabled = True
    try:
        got_429 = False
        for _ in range(12):
            r = client.post(
                "/api/v1/auth/register",
                json={"username": f"rate_{uuid.uuid4().hex[:8]}", "password": "pass123456"},
            )
            if r.status_code == 429:
                got_429 = True
                break
        assert got_429, "限流未生效：12 次注册全部通过"
    finally:
        app.state.limiter.enabled = False


# ==================== OSS presign（阶段3补充） ====================

def test_oss_presign(client):
    """已配置 OSS 时应返回三件套；未配置时报 503。"""
    _, _, token = make_user(client, "oss")
    r = client.get("/api/v1/oss/presign", params={"filename": "food.jpg"},
                   headers=auth_header(token))
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert {"uploadUrl", "contentType", "accessUrl"} <= set(body)
        assert body["contentType"] == "image/jpeg"
        assert body["accessUrl"].startswith("https://")


def test_oss_presign_requires_auth(client):
    r = client.get("/api/v1/oss/presign", params={"filename": "a.jpg"})
    assert r.status_code == 401
