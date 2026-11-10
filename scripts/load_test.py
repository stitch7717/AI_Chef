"""
吞吐基线压测（scripts/load_test.py）——基于通用框架 loadkit

分层验证系统能力：入口吞吐 / 数据库读 / 数据库写 / 多用户全流程 / 真实LLM并发。
业务级测试（尖峰/SSE/一致性/浸泡）见 load_test_pro.py。

用法：uv run python scripts/load_test.py [--base http://127.0.0.1:8080]
"""

import argparse
import asyncio

import httpx

from loadkit import rand_name, report, timed


async def register_and_login(c, prefix="lu"):
    u, pw = rand_name(prefix), "pass123456"
    await c.post("/api/v1/auth/register", json={"username": u, "password": pw})
    r = await c.post("/api/v1/auth/login", json={"username": u, "password": pw})
    return r.json()["access_token"]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--llm", type=int, default=3)
    args = ap.parse_args()

    async with httpx.AsyncClient(base_url=args.base.rstrip("/"), timeout=60,
                                 trust_env=False) as c:
        assert (await c.get("/")).status_code == 200, "前端入口不可用"
        token = await register_and_login(c)
        H = {"Authorization": f"Bearer {token}"}
        print(f"目标: {args.base}  压测账号就绪")

        results = []

        # 场景A：入口层吞吐（nginx 静态首页）
        async def a(i):
            return (await c.get("/")).status_code

        results.append(await timed("A 入口层 nginx 静态首页", a, 500, 100))

        # 场景B：数据库读
        async def b(i):
            return (await c.get("/api/v1/recipes", headers=H,
                                params={"page": 1, "page_size": 10})).status_code

        results.append(await timed("B 数据库读 GET /recipes", b, 300, 50))

        # 场景C：数据库写
        async def cc(i):
            return (await c.post("/api/v1/sessions", headers=H,
                                 json={"title": f"并发会话{i}"})).status_code

        results.append(await timed("C 数据库写 POST /sessions", cc, 100, 50))

        # 场景D：多虚拟用户完整流程（注册→登录→建会话→读菜谱）
        async def d(i):
            h = {"Authorization": f"Bearer {await register_and_login(c)}"}
            r1 = (await c.post("/api/v1/sessions", headers=h,
                               json={"title": "首次对话"})).status_code
            r2 = (await c.get("/api/v1/recipes", headers=h)).status_code
            return r1 if r1 >= 400 else r2

        results.append(await timed("D 多虚拟用户完整流程", d, 8, 8))

        # 场景E：真实 LLM 并发对话
        sids = [(await c.post("/api/v1/sessions", headers=H,
                              json={"title": f"LLM压测{i}"})).json()["id"]
                for i in range(args.llm)]
        questions = ["用一句话推荐一道快手菜", "鸡蛋过敏的人能吃什么菜",
                     "简单说说白灼虾的做法"]

        async def e(i):
            return (await c.post(f"/api/v1/chat/{sids[i]}/invoke", headers=H,
                                 json={"message": questions[i % len(questions)]},
                                 timeout=150)).status_code

        results.append(await timed(f"E {args.llm}路真实LLM对话并发", e, args.llm, args.llm))

    report(results)


if __name__ == "__main__":
    asyncio.run(main())
