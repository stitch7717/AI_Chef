"""
开发环境启动入口（run.py）

为什么要这个文件：两个 Windows 特有的坑叠加——
1. psycopg 异步模式不兼容 Windows 默认的 ProactorEventLoop，必须用 Selector；
2. uvicorn 在 Windows 上又硬编码使用 ProactorEventLoop（见 uvicorn/loops/asyncio.py），
   连 `--loop asyncio` 也绕不过去。

解法：自己用 Selector 策略创建事件循环，然后手动调 uvicorn.Server.serve()。
生产部署用 Linux/Docker 时无此问题，可直接 `uvicorn app.main:app`。

用法：
    uv run python run.py            # 默认 8002 端口
    uv run python run.py 8003       # 指定端口
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn


async def serve(port: int) -> None:
    config = uvicorn.Config(
        "app.main:app", host="127.0.0.1", port=port, log_level="info",
        proxy_headers=True,            # 信任反向代理头（nginx 传来的 X-Forwarded-For）
        forwarded_allow_ips="*",       # 容器网段内网可信；生产应收敛为 nginx 所在网段
        limit_concurrency=500,         # 超过则返回 503，防止过载雪崩（对标 Tomcat maxConnections）
    )
    server = uvicorn.Server(config)
    await server.serve()   # 在我们自己的 Selector 循环里运行


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    asyncio.run(serve(port))
