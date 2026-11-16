"""
全局限流单例（app/core/ratelimit.py）

背景：原来 auth.py 与 chat.py 各自 `Limiter(...)`，两套内存计数——
多实例各算各的、重启即清零，业务级要求的"全局限流"不成立。

这里收敛成一个实例，并优先使用 Redis 作为计数后端：
- Redis 可用 → 多实例共享计数（真限流）
- Redis 不可用 → 退回内存存储并告警（保证可用性，不因限流基础设施挂掉整个服务）
"""

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)


def _redis_available() -> bool:
    """探测 Redis 是否真的可连（Redis 是可选依赖，未安装/未启动都要能降级）。"""
    try:
        import redis  # 延迟导入：没装这个包也不影响服务启动

        client = redis.Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2
        )
        client.ping()
        return True
    except Exception as exc:  # noqa: BLE001 —— 任何异常都视为不可用
        logger.warning("Redis 不可用，限流退回进程内存（多实例不共享）：%s", exc)
        return False


_use_redis = _redis_available()

# 唯一实例：所有路由都从这里 import，禁止在各路由文件里再 new 一个
limiter = Limiter(
    key_func=get_remote_address,   # 反代场景由 uvicorn --proxy-headers 还原真实 IP
    **({"storage_uri": settings.REDIS_URL} if _use_redis else {}),
)

# 便于 /health 自检与日志排查：当前限流是否真的落在 Redis 上
LIMITER_BACKEND = "redis" if _use_redis else "memory"
