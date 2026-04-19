from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import ControlSystem, User
from app.schemas.machine import ControlSystemCreate, ControlSystemOut, ControlSystemUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/control-systems", tags=["control-systems"])


@router.get("", response_model=list[ControlSystemOut])
def list_control_systems(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[ControlSystem]:
    rows = db.execute(select(ControlSystem).where(ControlSystem.deleted_at.is_(None)).order_by(ControlSystem.name)).scalars().all()
    return list(rows)


@router.post("", response_model=ControlSystemOut, status_code=status.HTTP_201_CREATED)
def create_cs(
    body: ControlSystemCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> ControlSystem:
    c = ControlSystem(**body.model_dump())
    db.add(c)
    db.flush()
    log_action(db, entity_type="ControlSystem", entity_id=c.id, action="created", performed_by=actor.id, new_value={"name": c.name})
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{cs_id}", response_model=ControlSystemOut)
def update_cs(
    cs_id: int,
    body: ControlSystemUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> ControlSystem:
    c = db.get(ControlSystem, cs_id)
    if c is None or c.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old = {"name": c.name}
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    log_action(db, entity_type="ControlSystem", entity_id=c.id, action="updated", performed_by=actor.id, old_value=old, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{cs_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cs(
    cs_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    c = db.get(ControlSystem, cs_id)
    if c is None or c.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c.deleted_at = datetime.now(timezone.utc)
    log_action(db, entity_type="ControlSystem", entity_id=c.id, action="deleted", performed_by=actor.id, old_value={"name": c.name})
    db.commit()
