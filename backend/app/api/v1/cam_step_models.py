from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import CamStepModel, User
from app.schemas.cam_step_model import CamStepModelCreate, CamStepModelOut, CamStepModelUpdate
from app.services.audit_service import log_action
from app.services.toolchain_service import count_cases_for_cam_step_model

router = APIRouter(prefix="/cam-step-models", tags=["cam-step-models"])


@router.get("", response_model=list[CamStepModelOut])
def list_cam_step_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[CamStepModel]:
    rows = (
        db.execute(
            select(CamStepModel)
            .where(CamStepModel.deleted_at.is_(None))
            .order_by(CamStepModel.code)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.post("", response_model=CamStepModelOut, status_code=status.HTTP_201_CREATED)
def create_cam_step_model(
    body: CamStepModelCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> CamStepModel:
    m = CamStepModel(**body.model_dump())
    db.add(m)
    db.flush()
    log_action(
        db,
        entity_type="CamStepModel",
        entity_id=m.id,
        action="created",
        performed_by=actor.id,
        new_value={"code": m.code},
    )
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{row_id}", response_model=CamStepModelOut)
def update_cam_step_model(
    row_id: int,
    body: CamStepModelUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> CamStepModel:
    m = db.get(CamStepModel, row_id)
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    log_action(
        db,
        entity_type="CamStepModel",
        entity_id=m.id,
        action="updated",
        performed_by=actor.id,
        new_value=body.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cam_step_model(
    row_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    m = db.get(CamStepModel, row_id)
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if count_cases_for_cam_step_model(db, row_id) > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Step-/CAM-Modell ist noch Fällen zugeordnet und kann nicht entfernt werden.",
        )
    m.deleted_at = datetime.now(timezone.utc)
    log_action(db, entity_type="CamStepModel", entity_id=row_id, action="deleted", performed_by=actor.id, old_value={"code": m.code})
    db.commit()
