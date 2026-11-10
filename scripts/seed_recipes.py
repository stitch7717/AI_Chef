"""
菜谱数据导入脚本（scripts/seed_recipes.py）

用法：
    uv run python scripts/seed_recipes.py [源文件路径]

把 data/recipes.json 导入 lc-course-pro 的 recipes 表（按 name 幂等：重复执行只更新）。
容器启动时也会自动执行（见 docker-compose.yml 的 api 服务 command）。
"""

import asyncio
import json
import sys
from pathlib import Path

# 让脚本能找到 app 包（scripts 在项目根目录下一级）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.recipe import Recipe

# 默认用工程内数据（容器内外都可用）；也可命令行传入其他路径
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data" / "recipes.json"


async def main() -> None:
    recipes = json.loads(SOURCE.read_text(encoding="utf-8"))
    print(f"源文件共 {len(recipes)} 道菜")

    async with async_session_factory() as db:
        result = await db.execute(select(Recipe.name))
        existing = set(result.scalars().all())

        for item in recipes:
            payload = dict(
                name=item["name"],
                ingredients=json.dumps(item["ingredients"], ensure_ascii=False),
                difficulty=item.get("difficulty", "简单"),
                nutrition=item.get("nutrition", ""),
                steps=item.get("steps", ""),
                score_nutrition=item.get("score_nutrition"),
                score_ease=item.get("score_ease"),
            )
            if item["name"] in existing:
                row = (await db.execute(
                    select(Recipe).where(Recipe.name == item["name"])
                )).scalar_one()
                for k, v in payload.items():
                    setattr(row, k, v)
                print(f"  更新 {item['name']}")
            else:
                db.add(Recipe(**payload))
                print(f"  新增 {item['name']}")

        await db.commit()
    print("导入完成")


if __name__ == "__main__":
    # Windows 下 psycopg 异步需要 Selector 事件循环
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
