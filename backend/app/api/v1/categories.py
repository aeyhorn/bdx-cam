from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import ErrorCategory, User
from app.schemas.lookup import ErrorCategoryCreate, ErrorCategoryOut, ErrorCategoryUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[ErrorCategoryOut])
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[ErrorCategory]:
    rows = db.execute(select(ErrorCategory).order_by(ErrorCategory.name)).scalars().all()
    return list(rows)


@router.post("", response_model=ErrorCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    body: ErrorCategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> ErrorCategory:
    c = ErrorCategory(**body.model_dump())
    db.add(c)
    db.flush()
    log_action(db, entity_type="ErrorCategory", entity_id=c.id, action="created", performed_by=actor.id, new_value={"name": c.name})
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{cat_id}", response_model=ErrorCategoryOut)
def update_category(
    cat_id: int,
    body: ErrorCategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> ErrorCategory:
    c = db.get(ErrorCategory, cat_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old = {"name": c.name}
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    log_action(db, entity_type="ErrorCategory", entity_id=c.id, action="updated", performed_by=actor.id, old_value=old, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(c)
    return c
