"""认证路由（app/api/v1/auth.py）—— 对标 AuthController。"""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_user
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut
from app.services import auth_service

# 以客户端 IP 为限流键（生产环境前面有 Nginx 时要换成真实 IP 头）
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, data: UserCreate, db: AsyncSession = Depends(get_db)):
    """注册新用户（同 IP 每分钟最多 10 次，防刷）"""
    return await auth_service.register(db, data)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, data: UserLogin, db: AsyncSession = Depends(get_db)):
    """登录换取 JWT token"""
    return await auth_service.login(db, data.username, data.password)


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    """查看当前登录用户信息（需要 Bearer token）"""
    return user
