from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

security = HTTPBearer()

__all__ = ["get_db", "get_current_user", "require_roles"]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        uid = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from None
    user = db.execute(select(User).options(joinedload(User.role)).where(User.id == uid)).scalar_one_or_none()
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


def require_roles(*allowed_keys: str) -> Callable[[User], User]:
    def _inner(user: Annotated[User, Depends(get_current_user)]) -> User:
        key = user.role.key
        if key not in allowed_keys:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _inner
