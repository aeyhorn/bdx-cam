from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import Priority, Severity, Status, User
from app.schemas.lookup import PriorityOut, SeverityOut, StatusCreate, StatusOut, StatusUpdate
from app.services.audit_service import log_action

router = APIRouter(tags=["lookup"])


@router.get("/severities", response_model=list[SeverityOut])
def list_severities(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Severity]:
    rows = db.execute(select(Severity).order_by(Severity.sort_order, Severity.id)).scalars().all()
    return list(rows)


@router.get("/priorities", response_model=list[PriorityOut])
def list_priorities(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Priority]:
    rows = db.execute(select(Priority).order_by(Priority.sort_order, Priority.id)).scalars().all()
    return list(rows)


@router.get("/statuses", response_model=list[StatusOut])
def list_statuses(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Status]:
    rows = db.execute(select(Status).order_by(Status.sort_order, Status.id)).scalars().all()
    return list(rows)


@router.post("/statuses", response_model=StatusOut, status_code=status.HTTP_201_CREATED)
def create_status(
    body: StatusCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> Status:
    s = Status(**body.model_dump())
    db.add(s)
    db.flush()
    log_action(db, entity_type="Status", entity_id=s.id, action="created", performed_by=actor.id, new_value={"key": s.key})
    db.commit()
    db.refresh(s)
    return s


@router.patch("/statuses/{status_id}", response_model=StatusOut)
def update_status(
    status_id: int,
    body: StatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> Status:
    s = db.get(Status, status_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old = {"name": s.name, "sort_order": s.sort_order}
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    log_action(db, entity_type="Status", entity_id=s.id, action="updated", performed_by=actor.id, old_value=old, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(s)
    return s
