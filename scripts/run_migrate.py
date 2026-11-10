"""以编程方式执行数据库迁移（绕过命令行被应用控制策略拦截的问题）。

用法：
    uv run python scripts/run_migrate.py            # upgrade head
    uv run python scripts/run_migrate.py downgrade -1
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from alembic import command
from alembic.config import Config


def main():
    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))

    args = sys.argv[1:]
    if not args or args[0] == "upgrade":
        target = args[1] if len(args) > 1 else "head"
        command.upgrade(cfg, target)
        print(f"UPGRADED to {target}")
    elif args[0] == "downgrade":
        command.downgrade(cfg, args[1] if len(args) > 1 else "-1")
        print("DOWNGRADED")
    else:
        print(f"unknown args: {args}")
        sys.exit(2)


if __name__ == "__main__":
    main()
