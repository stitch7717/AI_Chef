# AI 大厨 · AI Chef

> 一个能看图、懂菜谱、记得你口味的私人厨师。面向个人饮食场景的 AI 应用：拍照或描述现有食材，自动给出带克数、步骤与营养的菜谱。

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-42B883?logo=vue.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)

## 功能

- **AI 对话**：多轮对话 + 流式输出，支持上传冰箱/食材照片识别；优先检索本地菜谱库，未命中自动联网搜索
- **菜谱发现**：123 道菜（家常菜 + 八大菜系名菜），瀑布流卡片、搜索、收藏、做完评分
- **食材库存**：137 种食材知识库（配图 + 平均重量），单位只用 7 种精确单位，支持「3 个番茄 ≈ 600g」自动折算
- **多用户隔离**：JWT 鉴权，会话/库存/收藏按用户隔离，越权访问一律 404

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI · SQLAlchemy 2.0 async · Pydantic v2 · Alembic · slowapi（限流） |
| AI 编排 | LangGraph `create_react_agent` · DeepSeek（deepseek-flash，原生识图）· Tavily 联网 · AsyncPostgresSaver（对话记忆） |
| 检索 | PostgreSQL 16 + pgvector（余弦相似度）· fastembed 本地向量化（BAAI/bge-small-zh-v1.5，512 维）· 混合重排（向量 + 同义词 + 字面重合） |
| 前端 | Vue 3 · Vite · Pinia · Vue Router · Element Plus（自建 Orea 风格设计系统） |
| 基础设施 | Docker Compose（postgres / redis / api / web）· Nginx（反代 + SSE + gzip + 强缓存）· 阿里云 OSS 预签名直传 |
| 质量 | pytest 26 用例 · 自研业务级压测（5 基线 + 4 业务场景） |

## 架构

```
浏览器 ──► Nginx (:8080) ──► FastAPI (:8002)
              │                ├─ api/v1   路由层（鉴权依赖、参数校验）
              │                ├─ services  业务层（事务、业务规则）
              │                ├─ repositories 数据访问层
              │                └─ agents    LangGraph Agent
              │                          ├─ search_local_recipes ──► pgvector 检索
              │                          └─ TavilySearch ─────────► 联网搜索
              │                │
              │                ├─ PostgreSQL 16 (+pgvector)：业务表 + 向量 + 对话记忆
              │                └─ Redis 7
              └─ 静态资源（前端构建产物 + 菜谱/食材图片，gzip + immutable 缓存）
```

**一次对话的执行链路**：用户提问 → 判断是否需要图片 → Agent 调 `search_local_recipes`（向量召回 + 词面重排，阈值 0.55 判定命中）→ 未命中转 `TavilySearch` → 模型整合成结构化菜谱 → SSE 逐 token 推送 → 结束后双写消息落库。

## 快速开始

### 1. 准备配置

```bash
cp .env.example .env
# 填入：POSTGRES_PASSWORD / JWT_SECRET_KEY / DEEPSEEK_API_KEY / TAVILY_API_KEY / OSS_*
```

### 2. 一键启动（Docker）

```bash
docker compose up -d --build
```

启动过程会自动完成：建表迁移 → 导入菜谱 → 补齐向量 → 起服务。

| 入口 | 地址 |
|---|---|
| Web 应用 | http://127.0.0.1:8080 |
| API 文档（Swagger） | http://127.0.0.1:8003/docs |
| 前端本地开发 | `cd frontend && npm install && npm run dev` → http://localhost:5173 |

> **向量模型**：`model_cache/` 不入库（约 91MB）。首次启动会通过 `HF_ENDPOINT` 镜像自动下载 `bge-small-zh-v1.5`；离线环境可自行下载后放入 `model_cache/` 再构建镜像。

### 3. 本地开发（不用整栈容器）

```bash
docker compose up -d postgres redis        # 只起数据库
uv sync                                    # 装依赖
uv run alembic upgrade head                # 迁移
uv run python scripts/seed_recipes.py      # 导入 123 道菜谱
uv run python run.py                       # 启动后端（Windows 必须用 run.py）
```

> Windows 上不要直接 `uvicorn app.main:app`：uvicorn 硬编码 Proactor 事件循环，与 asyncpg 不兼容，`run.py` 里显式切到 SelectorEventLoop。

## 接口一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/register` `/login` | 注册 / 登录（10 次/分钟限流） |
| GET | `/api/v1/auth/me` | 当前用户 |
| GET/POST/DELETE | `/api/v1/sessions` | 会话管理 |
| POST | `/api/v1/chat/{id}/stream` | **SSE 流式对话**（start/token/done/error） |
| POST | `/api/v1/chat/{id}/invoke` | 非流式对话（测试用） |
| GET/POST/PATCH/DELETE | `/api/v1/pantry` | 库存（原子 upsert） |
| GET | `/api/v1/recipes` `/recipes/search` | 菜谱列表（分页上限 200）/ 搜索 |
| POST/DELETE | `/api/v1/favorites/{recipe_id}` | 收藏（幂等） |
| POST | `/api/v1/feedbacks` | 评分反馈 |
| GET | `/api/v1/oss/presign` | OSS 直传签名 |

## 数据资产

| 资产 | 数量 | 说明 |
|---|---|---|
| 菜谱 | 123 道 | 家常菜 + 八大菜系 + 地方名菜，含食材/步骤/营养，100% 配真实图片（本地托管） |
| 食材知识库 | 137 种 | 图片 + 分类 + 平均单个重量 + 默认单位，驱动「个/条/片 → 克」换算 |
| 图片 | 260 张 | 统一压缩至 720px / JPEG q80，总量 17MB（原始 121MB，-87%） |

## 测试与压测

```bash
uv run pytest tests/ -q                     # 26 个用例：认证、会话隔离、SSE 协议、RAG、并发语义、分页边界
uv run python scripts/load_test_pro.py      # 业务级压测：尖峰 / 写一致性 / SSE 并发 / 浸泡
```

关键指标：300 并发尖峰 0 错误；30 分钟浸泡 1800 请求 0 错误、内存 311.8→311.6MB；8 并发注册 7.2s → 957ms（bcrypt 移入线程池）。

## 工程文档

- [`docs/AI大厨模块实现详解-开发者视角.docx`](docs) —— 每个模块的设计取舍与关键实现
- [`docs/AI大厨项目问题复盘-面试答辩.docx`](docs) —— 22 个真实问题的根因、定位过程与解决方案

## 目录结构

```
app/
  api/v1/         路由层：auth / sessions / chat / pantry / recipes / favorites / feedbacks / oss
  services/       业务层
  repositories/   数据访问层
  models/         7 张表（users / chat_sessions / chat_messages / pantry_items / recipes+向量 / favorites / feedbacks）
  agents/         personal_chief（Agent 装配）/ recipe_rag（混合检索）/ embedding（fastembed）
  core/           config / db / security（bcrypt + JWT）
frontend/         Vue 3 工程（登录 / 对话 / 库存 / 发现四页 + 移动端底部导航）
scripts/          seed_recipes / fetch_recipe_images / fetch_ingredients / load_test_pro
tests/            pytest 用例
data/             菜谱源数据（recipes.json）
alembic/          数据库迁移
```

## License

MIT
