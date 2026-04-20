from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import Case, CaseTestCase, TestCase, User
from app.schemas.test_case import TestCaseCreate, TestCaseOut, TestCaseUpdate
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable

router = APIRouter(tags=["test-cases"])


@router.get("/test-cases", response_model=list[TestCaseOut])
def list_test_cases(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[TestCase]:
    rows = db.execute(select(TestCase).options(joinedload(TestCase.machine)).order_by(TestCase.id.desc())).scalars().all()
    return list(rows)


@router.get("/test-cases/{tc_id}", response_model=TestCaseOut)
def get_tc(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = db.execute(select(TestCase).options(joinedload(TestCase.machine)).where(TestCase.id == tc_id)).scalar_one_or_none()
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return tc


@router.delete("/test-cases/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tc(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    log_action(db, entity_type="TestCase", entity_id=tc_id, action="deleted", performed_by=user.id, old_value={"title": tc.title})
    db.delete(tc)
    db.commit()


@router.post("/test-cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_tc(
    body: TestCaseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = TestCase(**body.model_dump())
    db.add(tc)
    db.flush()
    log_action(
        db,
        entity_type="TestCase",
        entity_id=tc.id,
        action="created",
        performed_by=user.id,
        new_value={"title": tc.title},
    )
    db.commit()
    return db.execute(select(TestCase).options(joinedload(TestCase.machine)).where(TestCase.id == tc.id)).scalar_one()


@router.patch("/test-cases/{tc_id}", response_model=TestCaseOut)
def patch_tc(
    tc_id: int,
    body: TestCaseUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(tc, k, v)
    log_action(db, entity_type="TestCase", entity_id=tc.id, action="updated", performed_by=user.id, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    return db.execute(select(TestCase).options(joinedload(TestCase.machine)).where(TestCase.id == tc.id)).scalar_one()


@router.post("/cases/{case_id}/link-test-case/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def link_test_case(
    case_id: int,
    test_case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    tc = db.get(TestCase, test_case_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Test case not found")
    exists = db.execute(
        select(CaseTestCase.id).where(
            CaseTestCase.case_id == case_id, CaseTestCase.test_case_id == test_case_id
        )
    ).scalar_one_or_none()
    if exists is not None:
        return None
    db.add(CaseTestCase(case_id=case_id, test_case_id=test_case_id))
    log_action(
        db,
        entity_type="CaseTestCase",
        entity_id=case_id,
        action="linked_test_case",
        performed_by=user.id,
        new_value={"test_case_id": test_case_id},
        case_id=case_id,
    )
    db.commit()
    return None


@router.delete("/cases/{case_id}/link-test-case/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_test_case(
    case_id: int,
    test_case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    row = db.execute(
        select(CaseTestCase).where(
            CaseTestCase.case_id == case_id, CaseTestCase.test_case_id == test_case_id
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    db.delete(row)
    log_action(
        db,
        entity_type="CaseTestCase",
        entity_id=case_id,
        action="unlinked_test_case",
        performed_by=user.id,
        new_value={"test_case_id": test_case_id},
        case_id=case_id,
    )
    db.commit()
    return None
