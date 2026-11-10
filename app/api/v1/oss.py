"""
OSS 签名直传接口（app/api/v1/oss.py）—— 纯标准库实现

为什么不用 alibabacloud-oss-v2 SDK：SDK 依赖 pycryptodome 的原生 .pyd 模块，
在这台机器上被"应用程序控制策略"拦截（WinError 4551）。而 OSS V1 预签名
算法本身非常简单，用标准库 hmac/sha1/base64 十几行就能实现——零原生依赖。

算法（OSS V1 预签名 PUT）：
    StringToSign = "PUT\n" + Content-MD5 + "\n" + Content-Type + "\n"
                 + Expires + "\n" + /{bucket}/{key}
    Signature = base64(hmac-sha1(AccessKeySecret, StringToSign))
    URL = https://{bucket}.{endpoint}/{key}?OSSAccessKeyId=..&Expires=..&Signature=..

对标 demo 的升级：
1. JWT 保护——只有登录用户才能拿到上传通行证
2. 对象 key 加 user_id 前缀（{uid}/{时间戳}_{文件名}）——不同用户互不覆盖
"""

import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/oss", tags=["图片直传"])

CONTENT_TYPE_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def presign_put_url(key: str, content_type: str, expires_ts: int) -> str:
    """生成 OSS V1 预签名 PUT URL（纯标准库）。"""
    string_to_sign = f"PUT\n\n{content_type}\n{expires_ts}\n/{settings.OSS_BUCKET}/{key}"
    signature = base64.b64encode(
        hmac.new(
            settings.OSS_ACCESS_KEY_SECRET.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    return (
        f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}/{quote(key)}"
        f"?OSSAccessKeyId={quote(settings.OSS_ACCESS_KEY_ID)}"
        f"&Expires={expires_ts}&Signature={quote(signature)}"
    )


@router.get("/presign")
def get_presign_url(filename: str, user: User = Depends(get_current_user)):
    """生成限时（1小时）上传通行证。"""
    if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_BUCKET:
        raise HTTPException(status_code=503, detail="OSS 未配置，请在 .env 中填写 OSS 密钥")

    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

    # 用户隔离的 key：避免重名互相覆盖，也方便按用户清理
    key = f"{user.id}/{int(time.time() * 1000)}_{filename}"
    expires_ts = int(
        datetime.now(timezone.utc).timestamp()
    ) + 3600

    return {
        "uploadUrl": presign_put_url(key, content_type, expires_ts),
        "contentType": content_type,
        "accessUrl": f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}/{quote(key)}",
    }
