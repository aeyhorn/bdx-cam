from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import AgentRun, Case, KnowledgeEntry, TestCase
from app.services.agent_executor import AgentExecutor
from app.services.agent_types import RunPayload
from app.services.audit_service import log_action


def create_queued_agent_run(
    db: Session,
    *,
    started_by: int | None,
    case_id: int | None = None,
    test_case_id: int | None = None,
    trigger_mode: str = "manual",
    agent_type: str = "error_analysis_and_codegen_improvement",
) -> AgentRun:
    run = AgentRun(
        case_id=case_id,
        test_case_id=test_case_id,
        trigger_mode=trigger_mode,
        agent_type=agent_type,
        status="queued",
        started_by=started_by,
        started_at=None,
        finished_at=None,
        error_message=None,
    )
    db.add(run)
    db.flush()
    return run


def process_agent_run_task(run_id: int) -> None:
    db = SessionLocal()
    try:
        run = db.get(AgentRun, run_id)
        if run is None:
            return
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.finished_at = None
        run.error_message = None
        db.commit()

        c = db.get(Case, run.case_id) if run.case_id is not None else None
        tc = db.get(TestCase, run.test_case_id) if run.test_case_id is not None else None

        payload = RunPayload(
            case_id=c.id if c else None,
            test_case_id=tc.id if tc else None,
            ticket_no=c.ticket_no if c else None,
            title=c.title if c else tc.title if tc else None,
            description=c.description if c else tc.description if tc else None,
            trigger_mode=run.trigger_mode or "manual",
            context={"source": "background-task", "run_id": run.id},
        )
        result = AgentExecutor().run(payload)

        ke = KnowledgeEntry(
            title=result.knowledge_title,
            symptom=result.knowledge_symptom,
            cause=result.knowledge_cause,
            resolution=result.knowledge_resolution,
            created_by=run.started_by or 1,
            updated_by=run.started_by or 1,
        )
        db.add(ke)
        db.flush()

        run.input_snapshot = payload.model_dump()
        run.output_summary = result.output_summary
        run.output_structured = result.output_structured
        run.knowledge_entry_id = ke.id
        run.model_name = result.model_name
        run.model_version = result.model_version
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = None
        log_action(
            db,
            entity_type="AgentRun",
            entity_id=run.id,
            action="completed",
            performed_by=run.started_by,
            new_value={"status": run.status, "knowledge_entry_id": run.knowledge_entry_id},
            case_id=run.case_id,
        )
        db.commit()
    except Exception as ex:  # noqa: BLE001
        run = db.get(AgentRun, run_id)
        if run is not None:
            run.status = "failed"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = str(ex)
            log_action(
                db,
                entity_type="AgentRun",
                entity_id=run.id,
                action="failed",
                performed_by=run.started_by,
                new_value={"status": run.status, "error": run.error_message},
                case_id=run.case_id,
            )
            db.commit()
    finally:
        db.close()

