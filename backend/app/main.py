from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.models.chunk import Chunk

# 让模型被 import，SQLAlchemy 才知道要创建哪些表
from app.models.user import User  # noqa: F401
from app.models.file import File  # noqa
from app.routes.auth import router as auth_router
from app.routes.files import router as files_router


app = FastAPI(title="Smart Assistant API")


app.include_router(auth_router)
app.include_router(files_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    # MVP阶段先用“启动时建表”，后面再换 Alembic migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)