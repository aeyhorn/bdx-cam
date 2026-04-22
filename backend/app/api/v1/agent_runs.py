from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core import roles as R
from app.models import AgentRun, Case, TestCase, User
from app.schemas.agent_run import AgentRunOut, AgentRunStart
from app.services.agent_run_service import create_queued_agent_run, process_agent_run_task
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@router.post("/start", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def start_agent_run(
    body: AgentRunStart,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING, R.FEEDBACK_PRODUCTION))],
) -> AgentRun:
    if body.case_id is None and body.test_case_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Either case_id or test_case_id is required")
    if body.case_id is not None and body.test_case_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Only one of case_id/test_case_id is allowed")

    c: Case | None = None
    tc: TestCase | None = None
    if body.case_id is not None:
        c = db.get(Case, body.case_id)
        if c is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
        ensure_case_readable(user, c)
    if body.test_case_id is not None:
        tc = db.get(TestCase, body.test_case_id)
        if tc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Test case not found")

    run = create_queued_agent_run(
        db,
        started_by=user.id,
        case_id=c.id if c else None,
        test_case_id=tc.id if tc else None,
        trigger_mode=body.trigger_mode or "manual",
    )

    log_action(
        db,
        entity_type="AgentRun",
        entity_id=run.id,
        action="queued",
        performed_by=user.id,
        new_value={"case_id": run.case_id, "test_case_id": run.test_case_id, "status": run.status},
        case_id=run.case_id,
    )
    db.commit()
    db.refresh(run)
    background_tasks.add_task(process_agent_run_task, run.id)
    return run


@router.get("/case/{case_id}", response_model=list[AgentRunOut])
def list_case_agent_runs(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING, R.FEEDBACK_PRODUCTION))],
) -> list[AgentRun]:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    rows = db.execute(select(AgentRun).where(AgentRun.case_id == case_id).order_by(AgentRun.id.desc())).scalars().all()
    return list(rows)


@router.post("/{run_id}/retry", response_model=AgentRunOut)
def retry_agent_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    if run.case_id is not None:
        c = db.get(Case, run.case_id)
        if c is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
        ensure_case_readable(user, c)
    run.status = "queued"
    run.error_message = None
    run.started_by = user.id
    log_action(
        db,
        entity_type="AgentRun",
        entity_id=run.id,
        action="retry_queued",
        performed_by=user.id,
        new_value={"status": run.status},
        case_id=run.case_id,
    )
    db.commit()
    db.refresh(run)
    background_tasks.add_task(process_agent_run_task, run.id)
    return run

