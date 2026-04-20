from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import MachinePostBinding, User
from app.schemas.machine_post_binding import MachinePostBindingCreate, MachinePostBindingOut, MachinePostBindingUpdate
from app.services.audit_service import log_action
from app.services.toolchain_service import count_cases_for_binding

router = APIRouter(prefix="/machine-post-bindings", tags=["machine-post-bindings"])

_LOAD = (
    joinedload(MachinePostBinding.machine),
    joinedload(MachinePostBinding.post_processor_version),
    joinedload(MachinePostBinding.control_system),
)


@router.get("", response_model=list[MachinePostBindingOut])
def list_bindings(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[MachinePostBinding]:
    rows = (
        db.execute(select(MachinePostBinding).options(*_LOAD).order_by(MachinePostBinding.id.desc()))
        .scalars()
        .all()
    )
    return list(rows)


@router.post("", response_model=MachinePostBindingOut, status_code=status.HTTP_201_CREATED)
def create_binding(
    body: MachinePostBindingCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> MachinePostBinding:
    b = MachinePostBinding(**body.model_dump())
    db.add(b)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Diese Kombination Maschine · Steuerung · Postprozessor existiert bereits.",
        ) from None
    log_action(
        db,
        entity_type="MachinePostBinding",
        entity_id=b.id,
        action="created",
        performed_by=actor.id,
        new_value=body.model_dump(),
    )
    db.commit()
    return db.execute(select(MachinePostBinding).options(*_LOAD).where(MachinePostBinding.id == b.id)).scalar_one()


@router.patch("/{binding_id}", response_model=MachinePostBindingOut)
def update_binding(
    binding_id: int,
    body: MachinePostBindingUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> MachinePostBinding:
    b = db.get(MachinePostBinding, binding_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    log_action(
        db,
        entity_type="MachinePostBinding",
        entity_id=b.id,
        action="updated",
        performed_by=actor.id,
        new_value=body.model_dump(exclude_unset=True),
    )
    db.commit()
    return db.execute(select(MachinePostBinding).options(*_LOAD).where(MachinePostBinding.id == b.id)).scalar_one()


@router.delete("/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_binding(
    binding_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    b = db.get(MachinePostBinding, binding_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if count_cases_for_binding(db, b) > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Freigabe wird noch von mindestens einem Fall verwendet (Maschine/Post/Steuerung).",
        )
    log_action(db, entity_type="MachinePostBinding", entity_id=binding_id, action="deleted", performed_by=actor.id)
    db.delete(b)
    db.commit()
