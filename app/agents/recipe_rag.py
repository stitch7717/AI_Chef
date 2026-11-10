"""
本地菜谱 RAG 检索（app/agents/recipe_rag.py）

相对 demo 的核心升级：向量存在 PostgreSQL 的 pgvector 列里（recipes.embedding），
多 worker / 重启共享一份索引，而不是每个进程各自在内存里建一遍。

检索逻辑（与 demo 一致）：
- 余弦相似度 >= 0.55 视为命中，返回 top-k 菜谱
- 全部低于阈值 → 明确返回"未命中"，让 Agent 转而联网搜索
"""

import re

from langchain_core.tools import tool
from sqlalchemy import text

from app.agents.embedding import embed_text, vector_to_pgstring
from app.core.db import async_session_factory

SIMILARITY_THRESHOLD = 0.55
TOP_K = 3

# 常见同义词归一：口语说法 → 菜谱库标准说法
SYNONYMS = [
    ("西红柿", "番茄"), ("洋柿子", "番茄"), ("马铃薯", "土豆"), ("洋芋", "土豆"),
    ("卷心菜", "包菜"), ("圆白菜", "包菜"), ("尖椒", "青椒"), ("鸡子", "鸡蛋"),
    ("大虾", "虾"), ("虾仁", "虾"), ("土豆丝", "土豆"), ("花椰菜", "花菜"),
    ("鸡子", "鸡蛋"), ("炒鸡蛋", "炒蛋"), ("鸡蛋羹", "蒸蛋"),
]
_NOISE = re.compile(r"[的了吗呢吧啊呀，,。.？?！!、\s]{1,}")
_LEX_WEIGHT = 0.35   # 词面命中权重（相对余弦相似度）


def _normalize(text_: str) -> str:
    """别名归一 + 去口语助词，用于词面匹配。"""
    s = str(text_)
    for a, b in SYNONYMS:
        s = s.replace(a, b)
    return _NOISE.sub("", s)


def _bigrams(s: str) -> set[str]:
    if len(s) <= 1:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


async def search_recipes_by_vector(query: str, top_k: int = TOP_K) -> list[dict]:
    """pgvector 语义检索：只返回相似度 >= 阈值的结果，全低于阈值则返回空列表
    （空列表代表'本地未命中'，Agent 会转用联网搜索）。"""
    query_vec = vector_to_pgstring(embed_text(query))
    sql = text("""
        SELECT name, ingredients, difficulty, nutrition,
               1 - (embedding <=> CAST(:qv AS vector)) AS similarity
        FROM recipes
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> CAST(:qv AS vector)) >= :threshold
        ORDER BY embedding <=> CAST(:qv AS vector)
        LIMIT :k
    """)
    fetch_k = max(top_k * 3, 8)   # 先取更多候选，再做词面重排
    async with async_session_factory() as db:
        rows = (await db.execute(
            sql, {"qv": query_vec, "k": fetch_k, "threshold": SIMILARITY_THRESHOLD}
        )).mappings().all()

    # 混合重排：语义相似度 + 菜名词面重合
    # 词面分 = 0.6×bigram Jaccard（词序相似）+ 0.4×字符覆盖率（抗短查询）
    q_norm = _normalize(query)
    q_big = _bigrams(q_norm)
    q_chars = set(q_norm)
    ranked = []
    for r in rows:
        item = dict(r)
        name_norm = _normalize(item["name"])
        name_big = _bigrams(name_norm)
        name_chars = set(name_norm)
        jac = len(q_big & name_big) / max(len(q_big | name_big), 1)
        cover = len(q_chars & name_chars) / max(len(q_chars), 1)
        lex = 0.6 * jac + 0.4 * cover
        item["lexical"] = lex
        item["score"] = item["similarity"] + _LEX_WEIGHT * lex
        ranked.append(item)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]


@tool("search_local_recipes")
async def search_local_recipes(query: str) -> str:
    """在本地菜谱库中按语义检索菜谱。当用户提到食材、想吃的菜、做法时优先使用本工具；
    只有本地没有合适结果时才使用联网搜索。"""
    results = await search_recipes_by_vector(query)
    if not results:
        return "本地菜谱库未命中（相似度低于阈值），请改用联网搜索。"
    lines = []
    for r in results:
        lines.append(
            f"【{r['name']}】相似度{r['similarity']:.2f} | 难度:{r['difficulty']} | "
            f"食材:{r['ingredients']} | 营养:{r['nutrition']}"
        )
    return "\n".join(lines)
