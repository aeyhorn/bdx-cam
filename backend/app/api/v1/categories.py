from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import ErrorCategory, KnowledgeEntry, RootCause, User
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


@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    cat_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    c = db.get(ErrorCategory, cat_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    n_rc = db.execute(select(func.count()).select_from(RootCause).where(RootCause.error_category_id == cat_id)).scalar_one()
    n_ke = db.execute(select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.error_category_id == cat_id)).scalar_one()
    if (n_rc or 0) > 0 or (n_ke or 0) > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Category in use; reassign or remove references first")
    log_action(db, entity_type="ErrorCategory", entity_id=cat_id, action="deleted", performed_by=actor.id, old_value={"name": c.name})
    db.delete(c)
    db.commit()
