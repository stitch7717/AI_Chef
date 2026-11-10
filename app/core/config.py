"""
全局配置（app/core/config.py）
================================

对标 Java 的 application.yml + @ConfigurationProperties：
所有配置项集中在一个 Settings 对象里，类型安全、启动即校验。

pydantic-settings 会自动从 .env 文件和环境变量读取；
字段类型写错（比如把数字写成字符串）会在启动时立刻报错，而不是运行到一半才炸。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # .env 里多余的项不报错
    )

    # ---- 数据层 ----
    DATABASE_URL: str                       # SQLAlchemy asyncpg 连接串
    DATABASE_URL_SYNC: str                  # Alembic 迁移用的同步连接串
    REDIS_URL: str = "redis://localhost:6380/0"

    # ---- JWT 认证 ----
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440          # token 有效期（分钟），默认 1 天

    # ---- 大模型 ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    TAVILY_API_KEY: str = ""

    # ---- OSS ----
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = ""
    OSS_REGION: str = "cn-shenzhen"
    OSS_ENDPOINT: str = "oss-cn-shenzhen.aliyuncs.com"


# 全局单例：任何模块都 from app.core.config import settings 直接用
settings = Settings()
