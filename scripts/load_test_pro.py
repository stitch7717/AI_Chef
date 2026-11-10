"""
业务级压测（scripts/load_test_pro.py）——基于通用框架 loadkit

在吞吐基线（load_test.py）之上验证业务级四类硬指标：
  场景F  尖峰冲击（spike）——瞬间 300 并发打读接口，验证过载保护与零 5xx
  场景G  SSE 流式并发——多路同时挂流式对话，验证流不串、不断、不积压
  场景H  并发写一致性——同一用户高并发收藏/加库存，验证无脏写（业务正确性）
  场景I  浸泡测试（soak）——持续混合负载 + api 容器内存采样，验证无泄漏

用法：uv run python scripts/load_test_pro.py [--soak-seconds 120] [--skip-soak]
"""

import argparse
import asyncio

import httpx

from loadkit import rand_name, report, soak, spike


async def register_and_login(c, prefix="bp"):
    u, pw = rand_name(prefix), "pass123456"
    await c.post("/api/v1/auth/register", json={"username": u, "password": pw})
    r = await c.post("/api/v1/auth/login", json={"username": u, "password": pw})
    return r.json()["access_token"]


async def scenario_spike(c, H):
    async def req(i):
        return (await c.get("/api/v1/recipes", headers=H,
                            params={"page": 1, "page_size": 5})).status_code
    return await spike("F 尖峰冲击：瞬时300并发读", req, 300)


async def scenario_sse(c, H, n=6):
    """n 路同时挂 SSE 流式对话，手动校验每路增量块数（spike 只量状态码）。"""
    print(f"\n[G SSE流式并发] {n} 路同时挂流")
    sids = []
    for i in range(n):
        sids.append((await c.post("/api/v1/sessions", headers=H,
                                  json={"title": f"SSE压测{i}"})).json()["id"])
    dishes = ["番茄炒蛋", "青椒肉丝", "蛋炒饭", "紫菜蛋花汤", "凉拌黄瓜", "麻婆豆腐"]

    async def one(i):
        chunks = 0
        t0 = time.perf_counter()
        async with c.stream(
            "POST", f"/api/v1/chat/{sids[i]}/stream", headers=H,
            json={"message": f"一句话介绍{dishes[i % len(dishes)]}的做法"}, timeout=120,
        ) as resp:
            if resp.status_code != 200:
                return resp.status_code, {"chunks": 0}
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    chunks += 1
        return resp.status_code, {"chunks": chunks, "sec": time.perf_counter() - t0}

    from loadkit import Result, print_result
    import time
    r = Result(name="G SSE流式并发", total=n)
    t0 = time.perf_counter()
    outs = await asyncio.gather(*(one(i) for i in range(n)))
    r.wall = time.perf_counter() - t0
    chunks = [o[1]["chunks"] for o in outs]
    r.extra["chunks_per_stream"] = chunks
    for i, (status, extra) in enumerate(outs):
        if status != 200:
            r.errors.append(f"HTTP {status}")
        elif extra["chunks"] < 3:
            r.errors.append(f"第{i}路仅{extra['chunks']}个增量（流式失效）")
    # 单路流式时长
    stream_secs = [o[1].get("sec", 0) for o in outs]
    r.extra["stream_seconds"] = stream_secs
    r.latencies = [s * 1000 for s in stream_secs]
    print_result(r)
    return r


async def scenario_consistency(c):
    """并发写一致性：同一用户高并发收藏与加库存，落库结果必须符合业务语义。"""
    from loadkit import Result, print_result
    import time
    results = []

    # H1 收藏：50 并发收藏同一菜谱 → 恰好 1 条
    H = {"Authorization": f"Bearer {await register_and_login(c)}"}
    recipes = (await c.get("/api/v1/recipes", headers=H)).json()
    rid = recipes[0]["id"]

    async def fav(i):
        import time as _t
        t0 = _t.perf_counter()
        code = (await c.post(f"/api/v1/favorites/{rid}", headers=H)).status_code
        return code, _t.perf_counter() - t0

    print("\n[H1 收藏并发一致性] 同一用户 50 并发收藏同一菜谱")
    r1 = Result(name="H1 收藏并发一致性", total=50)
    t0 = time.perf_counter()
    outs = await asyncio.gather(*(fav(i) for i in range(50)))
    r1.wall = time.perf_counter() - t0
    r1.latencies = [o[1] * 1000 for o in outs]
    codes = [o[0] for o in outs]
    favs = (await c.get("/api/v1/favorites", headers=H)).json()
    dup = sum(1 for f in favs if f["id"] == rid)
    r1.extra["db_rows"] = dup
    for code in codes:
        if code not in (200, 201):
            r1.errors.append(f"HTTP {code}")
    if dup != 1:
        r1.errors.append(f"收藏{dup}条（期望恰好1，脏写）")
    print_result(r1)
    results.append(r1)

    # H2 库存合并：30 并发添加同名食材 → 1 行且数量=30
    H2 = {"Authorization": f"Bearer {await register_and_login(c)}"}
    iname = rand_name("食材")

    async def add(i):
        import time as _t
        t0 = _t.perf_counter()
        code = (await c.post("/api/v1/pantry", headers=H2,
                             json={"name": iname, "quantity": 1, "unit": "个"})).status_code
        return code, _t.perf_counter() - t0

    print("\n[H2 库存并发合并] 同一用户 30 并发添加同名食材")
    r2 = Result(name="H2 库存并发合并", total=30)
    t0 = time.perf_counter()
    outs = await asyncio.gather(*(add(i) for i in range(30)))
    r2.wall = time.perf_counter() - t0
    r2.latencies = [o[1] * 1000 for o in outs]
    codes2 = [o[0] for o in outs]
    items = (await c.get("/api/v1/pantry", headers=H2)).json()
    same = [x for x in items if x["name"] == iname]
    total_qty = sum(x["quantity"] or 0 for x in same)
    r2.extra["db_rows"] = len(same)
    r2.extra["total_qty"] = total_qty
    for code in codes2:
        if code not in (200, 201):
            r2.errors.append(f"HTTP {code}")
    if len(same) != 1 or total_qty != 30:
        r2.errors.append(f"{len(same)}行/共{total_qty}个（期望1行30个，竞态）")
    print_result(r2)
    results.append(r2)
    return results


async def scenario_soak(c, H, seconds):
    async def req(i):
        if i % 10 < 7:
            return (await c.get("/api/v1/recipes", headers=H,
                                params={"page": 1, "page_size": 10})).status_code
        return (await c.post("/api/v1/sessions", headers=H,
                             json={"title": "soak"})).status_code
    return await soak("I 浸泡测试：持续混合负载", req, seconds=seconds, qps=15,
                      mem_container="lcp-api")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--soak-seconds", type=int, default=120)
    ap.add_argument("--skip-soak", action="store_true")
    args = ap.parse_args()

    async with httpx.AsyncClient(base_url=args.base.rstrip("/"), timeout=60,
                                 trust_env=False) as c:
        assert (await c.get("/")).status_code == 200, "前端入口不可用"
        token = await register_and_login(c)
        H = {"Authorization": f"Bearer {token}"}
        print(f"目标: {args.base}  压测账号就绪")

        results = [await scenario_spike(c, H),
                   await scenario_sse(c, H),
                   *await scenario_consistency(c)]
        if not args.skip_soak:
            results.append(await scenario_soak(c, H, args.soak_seconds))

    report(results)


if __name__ == "__main__":
    asyncio.run(main())
