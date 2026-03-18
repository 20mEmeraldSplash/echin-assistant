from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import math

from app.services.embedding_service import get_embedding
from app.db.session import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.file import File
from app.models.chunk import Chunk
from app.schemas.chat import ChatIn, ChatOut, Citation
from app.services.llm_service import generate_answer

router = APIRouter(prefix="/chat", tags=["chat"])

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

@router.post("", response_model=ChatOut)
async def chat(
    data: ChatIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) 确认 file 属于当前用户
    res = await db.execute(
        select(File).where(File.id == data.file_id, File.user_id == current_user.id)
    )
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if f.status != "READY":
        raise HTTPException(status_code=400, detail="File not processed yet")

    q = (data.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty query")

    # 2) 关键词检索：最简单版本（contains）
    # 先取出该文件的 chunks（MVP 小文件 OK；之后我们会优化成 DB 级全文检索或向量检索）
    res = await db.execute(
        select(Chunk).where(
            Chunk.user_id == current_user.id,
            Chunk.file_id == data.file_id,
        )
    )
    chunks = res.scalars().all()

    # 3) 打分：出现关键词次数越多分越高（超简单但能用）
    query_embedding = get_embedding(q)

    scored_chunks = []
    for c in chunks:
        if c.embedding:
            sim = cosine_similarity(query_embedding, c.embedding)
            scored_chunks.append((sim, c))

    ranked = sorted(scored_chunks, key=lambda x: x[0], reverse=True)
    top = [c for _, c in ranked[:5]]

    citations = []
    for c in top:
        snippet = c.text[:240].replace("\n", " ").strip()
        citations.append(Citation(page=c.page, snippet=snippet, chunk_id=c.id))

    # 4) MVP answer：先不调用大模型，直接拼“证据摘要”
    context = "\n\n".join(
        [f"[Page {c.page}]\n{c.text}" for c in top]
    )

    answer = generate_answer(
        query=q,
        context=context
    )

    return ChatOut(answer=answer, citations=citations)