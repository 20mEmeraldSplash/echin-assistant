import os
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.file import File
from app.auth.deps import get_current_user
from app.models.user import User

from typing import List
from app.schemas.files import FileOut

router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_DIR = "storage"


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    # 为当前用户创建目录
    user_folder = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    filepath = os.path.join(user_folder, file.filename)

    # 保存文件
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    # 记录数据库
    new_file = File(
        user_id=current_user.id,
        filename=file.filename,
        filepath=filepath,
        status="UPLOADED",
    )

    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    return {"file_id": new_file.id, "filename": new_file.filename}

@router.get("", response_model=List[FileOut])
async def list_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(File).where(File.user_id == current_user.id).order_by(File.id.desc())
    )
    files = res.scalars().all()
    return files