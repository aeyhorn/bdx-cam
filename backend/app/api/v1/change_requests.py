from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import Case, ChangeRequest, ChangeRequestCase, User
from app.schemas.change_request import ChangeRequestCreate, ChangeRequestOut, ChangeRequestUpdate
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable
from app.services.ticket_service import next_change_no

router = APIRouter(prefix="/change-requests", tags=["change-requests"])


@router.get("", response_model=list[ChangeRequestOut])
def list_change_requests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[ChangeRequest]:
    rows = db.execute(select(ChangeRequest).order_by(ChangeRequest.created_at.desc())).scalars().all()
    return list(rows)


@router.post("", response_model=ChangeRequestOut, status_code=status.HTTP_201_CREATED)
def create_cr(
    body: ChangeRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> ChangeRequest:
    cr = ChangeRequest(
        change_no=next_change_no(db),
        **body.model_dump(),
    )
    db.add(cr)
    db.flush()
    log_action(
        db,
        entity_type="ChangeRequest",
        entity_id=cr.id,
        action="created",
        performed_by=user.id,
        new_value={"change_no": cr.change_no, "title": cr.title},
    )
    db.commit()
    db.refresh(cr)
    return cr


@router.get("/{cr_id}", response_model=ChangeRequestOut)
def get_cr(
    cr_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> ChangeRequest:
    cr = db.get(ChangeRequest, cr_id)
    if cr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return cr


@router.patch("/{cr_id}", response_model=ChangeRequestOut)
def patch_cr(
    cr_id: int,
    body: ChangeRequestUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> ChangeRequest:
    cr = db.get(ChangeRequest, cr_id)
    if cr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old = {"status": cr.status, "title": cr.title}
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(cr, k, v)
    log_action(
        db,
        entity_type="ChangeRequest",
        entity_id=cr.id,
        action="updated",
        performed_by=user.id,
        old_value=old,
        new_value=body.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(cr)
    return cr


@router.post("/{cr_id}/link-case/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def link_case(
    cr_id: int,
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    cr = db.get(ChangeRequest, cr_id)
    if cr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Change request not found")
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    exists = db.execute(
        select(ChangeRequestCase.id).where(
            ChangeRequestCase.change_request_id == cr_id, ChangeRequestCase.case_id == case_id
        )
    ).scalar_one_or_none()
    if exists is not None:
        return None
    db.add(ChangeRequestCase(change_request_id=cr_id, case_id=case_id))
    log_action(
        db,
        entity_type="ChangeRequestCase",
        entity_id=cr_id,
        action="linked_case",
        performed_by=user.id,
        new_value={"case_id": case_id},
        case_id=case_id,
    )
    db.commit()
    return None
