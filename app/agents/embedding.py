"""
本地向量化服务（app/agents/embedding.py）

用 fastembed 跑 BAAI/bge-small-zh-v1.5（512 维，中文效果好）：
- 不依赖任何外部 API 密钥，模型文件首次运行自动下载（走 hf-mirror 国内镜像）
- 全局单例：模型加载约 1~2 秒，全进程只加载一次

对标 Java 里"一个 @Bean 管理的重资源对象"。
"""

import os

# HF 镜像必须在 fastembed/首次下载前生效（huggingface 国内直连不稳）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from fastembed import TextEmbedding  # noqa: E402

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBED_DIM = 512

# 缓存目录：本地开发默认在系统临时目录；容器里由 FASTEMBED_CACHE_DIR 指向打进镜像的模型
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR") or None

_model: TextEmbedding | None = None


def get_embed_model() -> TextEmbedding:
    """懒加载单例（首次调用才下载/加载模型）。"""
    global _model
    if _model is None:
        _model = TextEmbedding(
            model_name=MODEL_NAME,
            providers=["CPUExecutionProvider"],
            cache_dir=CACHE_DIR,
        )
    return _model


def embed_text(text: str) -> list[float]:
    """单条文本 → 向量。"""
    return list(next(get_embed_model().embed([text])))


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量文本 → 向量列表（比逐条快）。"""
    if not texts:
        return []
    return [list(v) for v in get_embed_model().embed(texts)]


def vector_to_pgstring(vec: list[float]) -> str:
    """把向量转成 pgvector 能识别的字面量：'[0.1,0.2,...]'。"""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
