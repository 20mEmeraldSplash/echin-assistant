from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import SignupIn, LoginIn, TokenOut, MeOut, ChangePasswordIn, MessageOut
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut)
async def signup(data: SignupIn, db: AsyncSession = Depends(get_db)):
    # email 是否已存在
    res = await db.execute(select(User).where(User.email == data.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id)
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == data.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user_id=user.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
async def me(current_user: User = Depends(get_current_user)):
    return MeOut(id=current_user.id, email=current_user.email)


@router.post("/change-password", response_model=MessageOut)
async def change_password(
    data: ChangePasswordIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """已登录用户修改密码（需输入当前密码）。忘记密码未登录场景需邮件重置，本接口不包含。"""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    if data.current_password == data.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")

    try:
        current_user.password_hash = hash_password(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return MessageOut(message="密码已更新")