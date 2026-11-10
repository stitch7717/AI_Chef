"""
菜谱图片抓取脚本（Tavily 版）scripts/fetch_recipe_images.py

用法（在 api 容器内执行）：
    docker exec lcp-api uv run python scripts/fetch_recipe_images.py

- 数据源：Tavily Search API（include_images=True），容器内已验证可达
- 按菜名搜图，取第一张可访问图片，写回 recipes.image_url
- 幂等：默认只处理 image_url 为空的行；--force 覆盖
"""

import asyncio
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session_factory
from app.models.recipe import Recipe

TAVILY = "https://api.tavily.com/search"


def search_image(query: str) -> str | None:
    """Tavily 搜图：返回第一张图片 URL 或 None。"""
    body = json.dumps({
        "api_key": settings.TAVILY_API_KEY,
        "query": f"{query} 菜谱 做法美食图片",
        "topic": "general",
        "max_results": 1,
        "include_images": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        TAVILY, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [warn] {query}: {e}")
        return None
    images = data.get("images") or []
    for img in images:
        # 旧版返回字符串数组，新版可能返回 {url, description} 对象
        url = img.get("url") if isinstance(img, dict) else img
        if url and url.startswith("http"):
            return url
    return None


async def main(force: bool = False) -> None:
    async with async_session_factory() as db:
        stmt = select(Recipe)
        if not force:
            stmt = stmt.where(Recipe.image_url.is_(None))
        rows = (await db.execute(stmt)).scalars().all()
        print(f"待抓取 {len(rows)} 道", flush=True)

        got, miss = 0, 0
        for row in rows:
            url = search_image(row.name)
            if url:
                row.image_url = url
                got += 1
                print(f"  v {row.name} -> {url[:90]}", flush=True)
            else:
                miss += 1
                print(f"  x {row.name} 未找到", flush=True)
            await db.commit()
            time.sleep(0.4)   # 限速防 429

        print(f"完成：命中 {got}，未命中 {miss}", flush=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(force="--force" in sys.argv))
