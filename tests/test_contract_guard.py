"""
契约守卫测试（tests/test_contract_guard.py）

目的：把"同一模式在不同路由里实现不一致"这类漏改，变成 CI 里的硬断言。
背景：会话分页漏加 Query 约束、注册漏捕 IntegrityError，都是"菜谱/收藏修了、另一处没修"。

覆盖：
1. 所有带 limit 的列表接口，传非法分页参数（-1 / 0 / 超大值）都必须 4xx，不能 5xx；
2. 写接口在"同键并发"下不能出现 5xx（唯一约束冲突要翻译成 409，而不是 500）。
"""

import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

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


def _user(client: TestClient, prefix: str = "guard"):
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    password = "pass123456"
    assert client.post(
        "/api/v1/auth/register", json={"username": username, "password": password}
    ).status_code == 201
    token = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]
    return username, password, {"Authorization": f"Bearer {token}"}


# ---------- 1. 列表接口的参数边界 ----------

LIST_ENDPOINTS = [
    "/api/v1/sessions",
    "/api/v1/recipes",
    "/api/v1/pantry",
]


@pytest.mark.parametrize("path", LIST_ENDPOINTS)
@pytest.mark.parametrize("query", ["limit=-1", "limit=0", "limit=1000000", "offset=-5"])
def test_list_endpoints_never_5xx(client, path, query):
    """任何列表接口拿到非法分页参数，都必须是 4xx——5xx 说明参数直接进了 SQL。"""
    _, _, h = _user(client)
    r = client.get(f"{path}?{query}", headers=h)
    assert r.status_code < 500, f"{path}?{query} 返回了 {r.status_code}：{r.text[:200]}"
    assert r.status_code in (200, 400, 422), (
        f"{path}?{query} 期望 4xx，实际 {r.status_code}"
    )


# ---------- 2. 写接口的并发唯一键冲突 ----------

def test_concurrent_register_same_name_no_5xx(client):
    """8 路并发注册同名：只允许 1 个 201，其余必须 409（不能 500）。"""
    username = f"race_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "password": "pass123456"}

    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda _: client.post("/api/v1/auth/register", json=payload).status_code, range(8)))

    assert all(c < 500 for c in codes), f"出现 5xx：{codes}"
    assert codes.count(201) == 1, f"应只有 1 个成功，实际 {codes}"
    assert codes.count(409) == 7, f"其余应为 409，实际 {codes}"


def test_concurrent_favorite_same_recipe_no_5xx(client):
    """8 路并发收藏同一菜谱：全部 2xx/3xx，且不能出现 5xx。"""
    _, _, h = _user(client, "fav")
    recipe_id = client.get("/api/v1/recipes?limit=1", headers=h).json()[0]["id"]

    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda _: client.post(f"/api/v1/favorites/{recipe_id}", headers=h).status_code, range(8)))

    assert all(c < 500 for c in codes), f"收藏出现 5xx：{codes}"


def test_concurrent_pantry_same_name_keeps_quantity(client):
    """10 路并发给同一食材 +1：最终数量必须等于 10（原子 upsert 的硬指标）。"""
    _, _, h = _user(client, "pan")
    name = f"并发食材_{uuid.uuid4().hex[:6]}"

    with ThreadPoolExecutor(max_workers=10) as ex:
        codes = list(ex.map(
            lambda _: client.post(
                "/api/v1/pantry", json={"name": name, "quantity": 1, "unit": "个"}, headers=h
            ).status_code,
            range(10),
        ))
    assert all(c < 500 for c in codes), f"库存出现 5xx：{codes}"

    items = client.get("/api/v1/pantry", headers=h).json()
    target = [i for i in items if i["name"] == name]
    assert len(target) == 1, f"同名应只有 1 行，实际 {len(target)}"
    assert target[0]["quantity"] == 10, f"数量应为 10，实际 {target[0]['quantity']}"


# ---------- 3. 输入白名单 ----------

@pytest.mark.parametrize("unit", ["克拉", "桶", "袋"])
def test_pantry_rejects_unknown_unit(client, unit):
    """单位白名单：模糊单位必须 422（它是"个→克"折算的依据）。"""
    _, _, h = _user(client, "unit")
    r = client.post(
        "/api/v1/pantry", json={"name": "怪单位", "quantity": 1, "unit": unit}, headers=h
    )
    assert r.status_code == 422, f"单位 {unit} 应被拒绝，实际 {r.status_code}"


def test_recipe_search_escapes_like_wildcards(client):
    """搜索 % 与 _ 必须被转义：不能返回任意菜谱。"""
    _, _, h = _user(client, "like")
    for kw in ("%", "_"):
        r = client.get("/api/v1/recipes/search", params={"keyword": kw}, headers=h)
        assert r.status_code == 200
        assert r.json() == [], f"关键字 {kw} 应返回空，实际 {len(r.json())} 条"
