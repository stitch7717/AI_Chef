"""pantry active-name unique index (concurrency-safe upsert)

Revision ID: a1f2c3d4e5b6
Revises: 8b38def77c77
Create Date: 2026-11-09

业务背景：库存合并原为「先查后改」，高并发下丢失更新（压测场景H2）。
本迁移先合并历史重复数据，再建部分唯一索引，之后服务层用
INSERT ... ON CONFLICT DO UPDATE 原子合并。
"""

import sqlalchemy as sa
from alembic import op

revision = "a1f2c3d4e5b6"
down_revision = "8b38def77c77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) 合并历史重复：同名未消耗的多行 → 保留最早一行，数量累加
    op.execute(
        """
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
    )
    # 2) 删除被合并的多余行
    op.execute(
        """
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
    )
    # 3) 部分唯一索引：仅约束未消耗行（已消耗的不限，可重复买同一名食材）
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pantry_active_name "
        "ON pantry_items (user_id, name) WHERE consumed = false;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_pantry_active_name;")
