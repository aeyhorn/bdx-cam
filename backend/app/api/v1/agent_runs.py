from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core import roles as R
from app.models import AgentRun, Case, KnowledgeEntry, TestCase, User
from app.schemas.agent_run import AgentRunOut, AgentRunStart
from app.services.agent_executor import AgentExecutor
from app.services.agent_types import RunPayload
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@router.post("/start", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def start_agent_run(
    body: AgentRunStart,
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

    payload = RunPayload(
        case_id=c.id if c else None,
        test_case_id=tc.id if tc else None,
        ticket_no=c.ticket_no if c else None,
        title=c.title if c else tc.title if tc else None,
        description=c.description if c else tc.description if tc else None,
        trigger_mode=body.trigger_mode or "manual",
        context={"source": "api:/agent-runs/start"},
    )
    result = AgentExecutor().run(payload)

    ke = KnowledgeEntry(
        title=result.knowledge_title,
        symptom=result.knowledge_symptom,
        cause=result.knowledge_cause,
        resolution=result.knowledge_resolution,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(ke)
    db.flush()

    run = AgentRun(
        case_id=c.id if c else None,
        test_case_id=tc.id if tc else None,
        trigger_mode=body.trigger_mode or "manual",
        agent_type="error_analysis_and_codegen_improvement",
        status="completed",
        input_snapshot=payload.model_dump(),
        output_summary=result.output_summary,
        output_structured=result.output_structured,
        knowledge_entry_id=ke.id,
        model_name=result.model_name,
        model_version=result.model_version,
        started_by=user.id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()

    log_action(
        db,
        entity_type="AgentRun",
        entity_id=run.id,
        action="started_and_completed",
        performed_by=user.id,
        new_value={"case_id": run.case_id, "test_case_id": run.test_case_id, "knowledge_entry_id": run.knowledge_entry_id},
        case_id=run.case_id,
    )
    db.commit()
    db.refresh(run)
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

