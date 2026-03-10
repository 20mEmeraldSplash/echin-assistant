from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_answer(query: str, context: str) -> str:
    prompt = f"""
You are a helpful assistant answering questions based only on the provided document excerpts.

Rules:
- Answer only using the provided context.
- If the answer is not in the context, say: "I couldn't find that in the uploaded PDF."
- Be concise and clear.
- Do not make up facts.

Context:
{context}

Question:
{query}
"""

    # 用 Chat Completions API（额度/限流与后台显示一致）
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return (response.choices[0].message.content or "").strip()