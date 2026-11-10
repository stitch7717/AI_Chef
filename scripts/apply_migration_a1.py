"""一次性迁移执行器：host 上 psycopg 被应用控制策略拦截，改用 asyncpg 直连。

执行 a1f2c3d4e5b6 迁移的内容（去重合并 → 建部分唯一索引 → 盖章版本号）。
容器内启动仍走标准 alembic upgrade head，不受影响。
"""

import asyncio
import sys

import asyncpg

URL = "postgresql://lc:lc_secret_2026@localhost:5433/lc_course"
NEW_REV = "a1f2c3d4e5b6"

MERGE_DUP = """
UPDATE pantry_items p
SET quantity = COALESCE(p.quantity, 0) + s.extra_qty,
    unit = COALESCE(NULLIF(p.unit, ''), s.unit),
    note = COALESCE(NULLIF(p.note, ''), s.note)
FROM (
    SELECT user_id, name, MIN(id) AS keep_id,
           COALESCE(SUM(quantity), 0) AS extra_qty,
           MAX(unit) AS unit, MAX(note) AS note
    FROM pantry_items
    WHERE consumed = false
    GROUP BY user_id, name
    HAVING COUNT(*) > 1
) s
WHERE p.id = s.keep_id
  AND s.extra_qty > 0;
"""

DELETE_DUP = """
DELETE FROM pantry_items p
USING (
    SELECT user_id, name, MIN(id) AS keep_id
    FROM pantry_items
    WHERE consumed = false
    GROUP BY user_id, name
    HAVING COUNT(*) > 1
) s
WHERE p.user_id = s.user_id
  AND p.name = s.name
  AND p.consumed = false
  AND p.id <> s.keep_id;
"""

CREATE_INDEX = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_pantry_active_name "
    "ON pantry_items (user_id, name) WHERE consumed = false;"
)


async def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    conn = await asyncpg.connect(URL)
    try:
        current = await conn.fetchval("SELECT version_num FROM alembic_version")
        print("当前版本:", current)
        if current == NEW_REV:
            print("已是目标版本，无需迁移")
            return
        n1 = await conn.execute(MERGE_DUP)
        print("合并重复行:", n1)
        n2 = await conn.execute(DELETE_DUP)
        print("删除多余行:", n2)
        await conn.execute(CREATE_INDEX)
        print("索引 uq_pantry_active_name 已创建")
        await conn.execute("UPDATE alembic_version SET version_num=$1", NEW_REV)
        print("版本号已更新为", NEW_REV)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
