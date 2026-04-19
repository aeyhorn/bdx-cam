from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import Machine, User
from app.schemas.machine import MachineCreate, MachineOut, MachineUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("", response_model=list[MachineOut])
def list_machines(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Machine]:
    rows = (
        db.execute(
            select(Machine)
            .options(joinedload(Machine.control_system))
            .where(Machine.deleted_at.is_(None))
            .order_by(Machine.name)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.post("", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine(
    body: MachineCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> Machine:
    m = Machine(**body.model_dump())
    db.add(m)
    db.flush()
    log_action(
        db,
        entity_type="Machine",
        entity_id=m.id,
        action="created",
        performed_by=actor.id,
        new_value={"name": m.name},
    )
    db.commit()
    return db.execute(select(Machine).options(joinedload(Machine.control_system)).where(Machine.id == m.id)).scalar_one()


@router.get("/{machine_id}", response_model=MachineOut)
def get_machine(
    machine_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Machine:
    m = db.execute(
        select(Machine).options(joinedload(Machine.control_system)).where(Machine.id == machine_id)
    ).scalar_one_or_none()
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Machine not found")
    return m


@router.patch("/{machine_id}", response_model=MachineOut)
def update_machine(
    machine_id: int,
    body: MachineUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> Machine:
    m = db.get(Machine, machine_id)
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Machine not found")
    old = {"name": m.name, "is_active": m.is_active}
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    log_action(db, entity_type="Machine", entity_id=m.id, action="updated", performed_by=actor.id, old_value=old, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    return db.execute(select(Machine).options(joinedload(Machine.control_system)).where(Machine.id == m.id)).scalar_one()


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(
    machine_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    m = db.get(Machine, machine_id)
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Machine not found")
    m.deleted_at = datetime.now(timezone.utc)
    log_action(db, entity_type="Machine", entity_id=m.id, action="deleted", performed_by=actor.id, old_value={"name": m.name})
    db.commit()
