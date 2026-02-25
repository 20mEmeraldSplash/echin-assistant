from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.db.session import get_db
from app.auth.security import decode_access_token
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = creds.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (KeyError, ValueError, jwt.PyJWTError):
        raise HTTPException(status_code=401, detail="Invalid token")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user