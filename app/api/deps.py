"""
公共依赖（app/api/deps.py）

对标 Java 里"拦截器 + SecurityContext"的组合：
- get_current_user 是所有受保护接口的门票——Router 函数加个参数
  `user: User = Depends(get_current_user)`，没带合法 token 的请求直接 401。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt as pyjwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories import user as user_repo

# HTTPBearer 让 Swagger /docs 出现 🔒 按钮，把 token 粘进去即可调试受保护接口
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="未登录，请在 Header 携带 Bearer token")
    try:
        user_id = decode_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效的 token")
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
