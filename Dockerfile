# 后端镜像（Linux 容器内无 Windows 事件循环问题，直接 uvicorn 启动）
FROM python:3.13-slim

WORKDIR /app

# 系统依赖：uv 安装 Python 依赖
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

# 应用代码
COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY tests ./tests
COPY alembic ./alembic
COPY alembic.ini run.py ./

# 向量模型离线打包（约91MB）：容器内不需要联网下载
COPY model_cache /app/model_cache
ENV FASTEMBED_CACHE_DIR=/app/model_cache

EXPOSE 8002

# 启动序：数据库迁移 → 导入菜谱 → 起服务（均为幂等操作，可重复执行）
CMD ["sh", "-c", "./.venv/bin/python -m alembic upgrade head && ./.venv/bin/python scripts/seed_recipes.py && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --proxy-headers --forwarded-allow-ips \"*\" --limit-concurrency 500"]
