from pydantic import BaseModel


class ChatIn(BaseModel):
    file_id: int
    query: str


class Citation(BaseModel):
    page: int
    snippet: str
    chunk_id: int


class ChatOut(BaseModel):
    answer: str
    citations: list[Citation]