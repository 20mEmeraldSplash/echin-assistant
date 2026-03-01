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
