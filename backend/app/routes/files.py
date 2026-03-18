import os
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.file import File
from app.auth.deps import get_current_user
from app.models.user import User

from app.models.chunk import Chunk
from app.services.pdf_processing import extract_pages_from_pdf
from app.services.chunking import chunk_text

from typing import List
from app.schemas.files import FileOut

from app.services.embedding_service import get_embedding

from sqlalchemy import delete

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

@router.post("/{file_id}/process")
async def process_pdf(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) 查文件且必须属于当前用户
    res = await db.execute(
        select(File).where(File.id == file_id, File.user_id == current_user.id)
    )
    file_rec = res.scalar_one_or_none()
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")

    if not file_rec.filepath.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    # 2) 更新状态
    file_rec.status = "PROCESSING"
    await db.commit()

    try:
        # 3) 先清理旧 chunks（如果重复处理）
        await db.execute(
            delete(Chunk).where(Chunk.file_id == file_rec.id, Chunk.user_id == current_user.id)
        )
        await db.commit()

        # 4) 读 PDF 每一页文本
        pages = extract_pages_from_pdf(file_rec.filepath)

        total_chunks = 0
        # 5) 每页切块并写库
        for page_idx, page_text in enumerate(pages, start=1):
            chunks = chunk_text(page_text, chunk_size=1000, overlap=150)
            for ci, ct in enumerate(chunks):
                emb = get_embedding(ct)

                db.add(
                    Chunk(
                        user_id=current_user.id,
                        file_id=file_rec.id,
                        page=page_idx,
                        chunk_index=ci,
                        text=ct,
                        source="pdf",
                        embedding=emb,
                    )
                )
            total_chunks += len(chunks)

        await db.commit()

        # 6) 标记 READY
        file_rec.status = "READY"
        await db.commit()

        return {
            "file_id": file_rec.id,
            "status": file_rec.status,
            "pages": len(pages),
            "chunks": total_chunks,
        }

    except Exception as e:
        file_rec.status = "FAILED"
        # 如果你加了 error_message 列，就取消下一行注释
        # file_rec.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {type(e).__name__}")