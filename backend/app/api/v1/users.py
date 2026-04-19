from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.core.roles import ADMIN
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ADMIN))],
) -> list[User]:
    rows = db.execute(select(User).options(joinedload(User.role)).where(User.deleted_at.is_(None))).scalars().all()
    return list(rows)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    exists = db.execute(select(User.id).where(User.email == body.email)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    u = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        password_hash=hash_password(body.password),
        role_id=body.role_id,
        is_active=True,
    )
    db.add(u)
    db.flush()
    log_action(
        db,
        entity_type="User",
        entity_id=u.id,
        action="created",
        performed_by=actor.id,
        new_value={"email": u.email, "role_id": u.role_id},
    )
    db.commit()
    db.refresh(u)
    u = db.execute(select(User).options(joinedload(User.role)).where(User.id == u.id)).scalar_one()
    return u


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    u = db.execute(select(User).options(joinedload(User.role)).where(User.id == user_id)).scalar_one_or_none()
    if u is None or u.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return u


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    u = db.get(User, user_id)
    if u is None or u.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    old = {"email": u.email, "role_id": u.role_id, "is_active": u.is_active}
    data = body.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        u.password_hash = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(u, k, v)
    log_action(
        db,
        entity_type="User",
        entity_id=u.id,
        action="updated",
        performed_by=actor.id,
        old_value=old,
        new_value={"email": u.email, "role_id": u.role_id, "is_active": u.is_active},
    )
    db.commit()
    return db.execute(select(User).options(joinedload(User.role)).where(User.id == u.id)).scalar_one()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    from datetime import datetime, timezone

    u = db.get(User, user_id)
    if u is None or u.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    u.deleted_at = datetime.now(timezone.utc)
    u.is_active = False
    log_action(db, entity_type="User", entity_id=u.id, action="deleted", performed_by=actor.id, old_value={"email": u.email})
    db.commit()
