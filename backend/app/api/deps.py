import uuid
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.errors import UnauthorizedError
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError(message="Missing or malformed Authorization header")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(message="Malformed user ID in token")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise UnauthorizedError(message="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user
