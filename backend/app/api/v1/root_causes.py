from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import Case, RootCause, User
from app.schemas.root_cause import RootCauseCreate, RootCauseOut, RootCauseUpdate
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable

router = APIRouter(tags=["root-causes"])


@router.get("/cases/{case_id}/root-cause", response_model=Optional[RootCauseOut])
def get_root_cause(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> RootCause | None:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    return db.execute(select(RootCause).where(RootCause.case_id == case_id)).scalar_one_or_none()


@router.post("/cases/{case_id}/root-cause", response_model=RootCauseOut, status_code=status.HTTP_201_CREATED)
def create_root_cause(
    case_id: int,
    body: RootCauseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> RootCause:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    exists = db.execute(select(RootCause.id).where(RootCause.case_id == case_id)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Root cause exists; use PATCH /root-causes/{id}")
    rc = RootCause(
        case_id=case_id,
        error_category_id=body.error_category_id,
        hypothesis=body.hypothesis,
        confirmed=body.confirmed,
        cps_reference=body.cps_reference,
        nc_pattern=body.nc_pattern,
        created_by=user.id,
    )
    db.add(rc)
    db.flush()
    log_action(
        db,
        entity_type="RootCause",
        entity_id=rc.id,
        action="created",
        performed_by=user.id,
        new_value={"case_id": case_id},
        case_id=case_id,
    )
    db.commit()
    db.refresh(rc)
    return rc


@router.patch("/root-causes/{root_cause_id}", response_model=RootCauseOut)
def patch_root_cause(
    root_cause_id: int,
    body: RootCauseUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> RootCause:
    rc = db.get(RootCause, root_cause_id)
    if rc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, rc.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    old = {
        "hypothesis": rc.hypothesis,
        "confirmed": rc.confirmed,
        "error_category_id": rc.error_category_id,
    }
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rc, k, v)
    log_action(
        db,
        entity_type="RootCause",
        entity_id=rc.id,
        action="updated",
        performed_by=user.id,
        old_value=old,
        new_value=body.model_dump(exclude_unset=True),
        case_id=rc.case_id,
    )
    db.commit()
    db.refresh(rc)
    return rc
