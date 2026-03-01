from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), index=True)

    page: Mapped[int] = mapped_column(index=True)
    chunk_index: Mapped[int] = mapped_column(index=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    # 预留：后面加 embedding vector
    # embedding: Mapped[list[float]] = mapped_column(...)
    source: Mapped[str] = mapped_column(String(50), default="pdf")

    def chunk_text(text: str, *, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
        """
        把长文本切成小段，带一点 overlap（重叠）帮助上下文连续。
        超简单版本，够 MVP 用。
        """
        text = (text or "").strip()
        if not text:
            return []

        chunks = []
        start = 0
        n = len(text)

        while start < n:
            end = min(start + chunk_size, n)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == n:
                break
            start = max(0, end - overlap)

        return chunks