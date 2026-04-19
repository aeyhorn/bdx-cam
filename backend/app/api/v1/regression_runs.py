from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import PostProcessorVersion, RegressionRun, TestCase, User
from app.schemas.test_case import RegressionRunCreate, RegressionRunOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/regression-runs", tags=["regression-runs"])


@router.get("", response_model=list[RegressionRunOut])
def list_regressions(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[RegressionRun]:
    rows = db.execute(select(RegressionRun).order_by(RegressionRun.id.desc())).scalars().all()
    return list(rows)


@router.post("", response_model=RegressionRunOut, status_code=status.HTTP_201_CREATED)
def create_regression(
    body: RegressionRunCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> RegressionRun:
    if db.get(TestCase, body.test_case_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid test_case_id")
    if db.get(PostProcessorVersion, body.post_processor_version_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid post_processor_version_id")
    ex_at = body.executed_at or datetime.now(timezone.utc)
    rr = RegressionRun(
        test_case_id=body.test_case_id,
        post_processor_version_id=body.post_processor_version_id,
        result=body.result,
        notes=body.notes,
        executed_by=user.id,
        executed_at=ex_at,
    )
    db.add(rr)
    db.flush()
    log_action(
        db,
        entity_type="RegressionRun",
        entity_id=rr.id,
        action="created",
        performed_by=user.id,
        new_value={"result": rr.result, "test_case_id": rr.test_case_id},
    )
    db.commit()
    db.refresh(rr)
    return rr
