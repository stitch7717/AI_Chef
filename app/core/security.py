"""
安全工具（app/core/security.py）
================================

对标 Java 的 Spring Security 密码编码器 + JwtUtil：

- bcrypt：自带随机盐、慢速抗暴力破解，业界标准（对应 Java 的 BCryptPasswordEncoder）
- PyJWT：签发/校验令牌（对应 jjwt 库）

设计要点：
- 密码只存哈希，永远不存明文、不打日志
- token 里只放 user_id（sub），不放敏感信息——JWT 本质是"可验证的明文"
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """明文密码 → bcrypt 哈希（每次结果不同，因为盐是随机的）。"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码：把明文用同一套算法哈希后与库里比对。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    """签发 JWT：payload = {sub: 用户ID, exp: 过期时间}。"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> int:
    """校验 JWT 并返回 user_id；无效/过期时抛 jwt 异常（由调用方转成 401）。"""
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return int(payload["sub"])
