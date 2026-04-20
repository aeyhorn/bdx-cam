from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.core import roles as R
from app.models import (
    AuditLog,
    Case,
    ChangeRequest,
    ChangeRequestCase,
    CaseTestCase,
    Machine,
    PostProcessorVersion,
    Priority,
    Status,
    TestCase,
    User,
)
from app.schemas.audit import AuditLogOut
from app.schemas.case import CaseCreate, CaseOut, CasePatch
from app.schemas.change_request import ChangeRequestOut
from app.schemas.test_case import TestCaseOut
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable, ensure_case_writable_production
from app.services.ticket_service import next_ticket_no
from app.services.toolchain_service import (
    require_approved_toolchain,
    require_cam_step_model,
    validate_generated_nc_attachment,
)

router = APIRouter(prefix="/cases", tags=["cases"])

_CASE_LOAD = (
    selectinload(Case.machine).selectinload(Machine.control_system),
    selectinload(Case.control_system),
    selectinload(Case.post_processor_version),
    selectinload(Case.cam_step_model),
    selectinload(Case.generated_nc_attachment),
    selectinload(Case.reporter),
    selectinload(Case.assignee),
    selectinload(Case.severity),
    selectinload(Case.priority),
    selectinload(Case.status),
)


def _load_case(db: Session, case_id: int) -> Case | None:
    return db.execute(select(Case).options(*_CASE_LOAD).where(Case.id == case_id)).scalar_one_or_none()


PRODUCTION_PATCH = frozenset(
    {
        "title",
        "description",
        "project_name",
        "part_name",
        "nc_line_reference",
        "expected_behavior",
        "actual_behavior",
    }
)


@router.get("", response_model=list[CaseOut])
def list_cases(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    search: str | None = None,
    status_id: int | None = None,
    machine_id: int | None = None,
) -> list[Case]:
    stmt = select(Case).options(*_CASE_LOAD)
    if not R.can_see_all_cases(user.role.key):
        stmt = stmt.where(Case.reporter_id == user.id)
    if status_id is not None:
        stmt = stmt.where(Case.status_id == status_id)
    if machine_id is not None:
        stmt = stmt.where(Case.machine_id == machine_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Case.title.ilike(like), Case.ticket_no.ilike(like), Case.nc_program_name.ilike(like)))
    stmt = stmt.order_by(Case.created_at.desc())
    rows = db.execute(stmt).scalars().all()
    return list(rows)


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    body: CaseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Case:
    if user.role.key not in (R.FEEDBACK_PRODUCTION, R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot create cases")
    st = db.execute(select(Status).where(Status.key == "NEW")).scalar_one_or_none()
    pr = db.execute(select(Priority).where(Priority.key == "NORMAL")).scalar_one_or_none()
    if st is None or pr is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing seed statuses/priorities")
    require_cam_step_model(db, body.cam_step_model_id)
    require_approved_toolchain(
        db,
        machine_id=body.machine_id,
        post_processor_version_id=body.post_processor_version_id,
        control_system_id=body.control_system_id,
    )
    ticket = next_ticket_no(db)
    c = Case(
        ticket_no=ticket,
        title=body.title,
        description=body.description,
        machine_id=body.machine_id,
        control_system_id=body.control_system_id,
        post_processor_version_id=body.post_processor_version_id,
        cam_step_model_id=body.cam_step_model_id,
        generated_nc_attachment_id=None,
        reporter_id=user.id,
        assignee_id=None,
        project_name=body.project_name,
        part_name=body.part_name,
        nc_program_name=body.nc_program_name,
        nc_line_reference=body.nc_line_reference,
        expected_behavior=body.expected_behavior,
        actual_behavior=body.actual_behavior,
        severity_id=body.severity_id,
        priority_id=pr.id,
        status_id=st.id,
    )
    db.add(c)
    db.flush()
    log_action(
        db,
        entity_type="Case",
        entity_id=c.id,
        action="created",
        performed_by=user.id,
        new_value={"ticket_no": c.ticket_no, "title": c.title},
        case_id=c.id,
    )
    db.commit()
    out = _load_case(db, c.id)
    assert out is not None
    return out


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Case:
    c = _load_case(db, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    return c


@router.patch("/{case_id}", response_model=CaseOut)
def patch_case(
    case_id: int,
    body: CasePatch,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Case:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    data = body.model_dump(exclude_unset=True)
    if not data:
        out = _load_case(db, case_id)
        assert out is not None
        return out

    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
        extra = set(data.keys()) - PRODUCTION_PATCH
        if extra:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Cannot update fields: {extra}")
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot update cases")

    old_snapshot: dict[str, Any] = {
        "status_id": c.status_id,
        "assignee_id": c.assignee_id,
        "priority_id": c.priority_id,
        "severity_id": c.severity_id,
    }
    for k, v in data.items():
        setattr(c, k, v)
    if {"machine_id", "post_processor_version_id", "control_system_id"} & data.keys():
        require_approved_toolchain(
            db,
            machine_id=c.machine_id,
            post_processor_version_id=c.post_processor_version_id,
            control_system_id=c.control_system_id,
        )
    if "cam_step_model_id" in data:
        require_cam_step_model(db, c.cam_step_model_id)
    if "generated_nc_attachment_id" in data:
        validate_generated_nc_attachment(db, c.id, c.generated_nc_attachment_id)
    db.flush()
    if "status_id" in data and data["status_id"] != old_snapshot["status_id"]:
        log_action(
            db,
            entity_type="Case",
            entity_id=c.id,
            action="status_changed",
            performed_by=user.id,
            old_value={"status_id": old_snapshot["status_id"]},
            new_value={"status_id": c.status_id},
            case_id=c.id,
        )
    if "assignee_id" in data and data.get("assignee_id") != old_snapshot["assignee_id"]:
        log_action(
            db,
            entity_type="Case",
            entity_id=c.id,
            action="assignee_changed",
            performed_by=user.id,
            old_value={"assignee_id": old_snapshot["assignee_id"]},
            new_value={"assignee_id": c.assignee_id},
            case_id=c.id,
        )
    log_action(
        db,
        entity_type="Case",
        entity_id=c.id,
        action="updated",
        performed_by=user.id,
        old_value=old_snapshot,
        new_value=data,
        case_id=c.id,
    )
    db.commit()
    out = _load_case(db, case_id)
    assert out is not None
    return out


@router.get("/{case_id}/history", response_model=list[AuditLogOut])
def case_history(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AuditLog]:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    rows = (
        db.execute(
            select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.created_at.desc()).limit(200)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.get("/{case_id}/relations")
def case_relations(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list]:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    cr_ids = db.execute(
        select(ChangeRequestCase.change_request_id).where(ChangeRequestCase.case_id == case_id)
    ).scalars().all()
    crs: list[ChangeRequest] = []
    if cr_ids:
        crs = list(db.execute(select(ChangeRequest).where(ChangeRequest.id.in_(cr_ids))).scalars().all())
    tc_ids = db.execute(select(CaseTestCase.test_case_id).where(CaseTestCase.case_id == case_id)).scalars().all()
    tcs: list[TestCase] = []
    if tc_ids:
        tcs = list(db.execute(select(TestCase).where(TestCase.id.in_(tc_ids))).scalars().all())
    return {
        "change_requests": [ChangeRequestOut.model_validate(x).model_dump() for x in crs],
        "test_cases": [TestCaseOut.model_validate(x).model_dump() for x in tcs],
    }
