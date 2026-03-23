from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: int
    email: EmailStr


class ChangePasswordIn(BaseModel):
    """已登录用户修改密码：需验证当前密码。"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


class MessageOut(BaseModel):
    message: str