from pypdf import PdfReader


def extract_pages_from_pdf(filepath: str) -> list[str]:
    """
    返回每一页的文本列表：pages_text[0] = 第1页文本
    """
    reader = PdfReader(filepath)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return pages_text