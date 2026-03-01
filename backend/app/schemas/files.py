from pydantic import BaseModel


class FileOut(BaseModel):
    id: int
    filename: str
    status: str

    class Config:
        from_attributes = True