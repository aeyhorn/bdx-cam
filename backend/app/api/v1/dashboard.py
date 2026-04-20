from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import (
    Case,
    ErrorCategory,
    Machine,
    PostProcessorVersion,
    RegressionRun,
    RootCause,
    Severity,
    Status,
    SystemBuildVersion,
    User,
)
from app.schemas.dashboard import AdminDashboard, EngineeringDashboard, LabelCount, ProductionDashboard, SystemBuildStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _case_brief(c: Case) -> dict[str, Any]:
    return {
        "id": c.id,
        "ticket_no": c.ticket_no,
        "title": c.title,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _build_statuses(db: Session) -> list[SystemBuildStatus]:
    rows = db.execute(
        select(SystemBuildVersion).order_by(
            SystemBuildVersion.component.asc(),
            SystemBuildVersion.build_no.desc(),
            SystemBuildVersion.id.desc(),
        )
    ).scalars().all()
    grouped: dict[str, list[SystemBuildVersion]] = {}
    for row in rows:
        grouped.setdefault(row.component, []).append(row)
    out: list[SystemBuildStatus] = []
    for component, items in grouped.items():
        latest = items[0]
        deployed = next((x for x in items if x.is_deployed), None)
        out.append(
            SystemBuildStatus(
                component=component,
                latest_build_no=latest.build_no,
                latest_version_label=latest.version_label,
                latest_created_at=latest.created_at,
                deployed_build_no=deployed.build_no if deployed else None,
                deployed_version_label=deployed.version_label if deployed else None,
                deployed_created_at=deployed.created_at if deployed else None,
                is_outdated=(deployed is None) or (deployed.id != latest.id),
            )
        )
    return out


@router.get("/production", response_model=ProductionDashboard)
def dash_production(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ProductionDashboard:
    closed_ids = list(
        db.execute(select(Status.id).where(Status.key.in_(["CLOSED", "REJECTED", "APPROVED"]))).scalars().all()
    )
    if closed_ids:
        my_open = (
            db.scalar(
                select(func.count()).select_from(Case).where(
                    Case.reporter_id == user.id, Case.status_id.not_in(closed_ids)
                )
            )
            or 0
        )
    else:
        my_open = db.scalar(select(func.count()).select_from(Case).where(Case.reporter_id == user.id)) or 0

    fb = db.execute(select(Status.id).where(Status.key == "FEEDBACK_REQUESTED")).scalar_one_or_none()
    open_q = 0
    if fb is not None:
        open_q = db.scalar(
            select(func.count()).select_from(Case).where(Case.reporter_id == user.id, Case.status_id == fb)
        ) or 0

    recent = db.execute(
        select(Case)
        .where(Case.reporter_id == user.id)
        .order_by(Case.created_at.desc())
        .limit(5)
    ).scalars().all()

    return ProductionDashboard(
        my_open_cases=int(my_open),
        open_questions=int(open_q),
        recent_cases=[_case_brief(x) for x in recent],
        system_builds=_build_statuses(db),
    )


@router.get("/engineering", response_model=EngineeringDashboard)
def dash_engineering(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> EngineeringDashboard:
    new_st = db.execute(select(Status.id).where(Status.key == "NEW")).scalar_one_or_none()
    new_cases = 0
    if new_st:
        new_cases = db.scalar(select(func.count()).select_from(Case).where(Case.status_id == new_st)) or 0

    crit = db.execute(select(Severity.id).where(Severity.key == "CRITICAL")).scalar_one_or_none()
    critical_cases = 0
    if crit:
        critical_cases = db.scalar(select(func.count()).select_from(Case).where(Case.severity_id == crit)) or 0

    unassigned = db.scalar(select(func.count()).select_from(Case).where(Case.assignee_id.is_(None))) or 0

    cases_without_root_cause = int(
        db.scalar(
            select(func.count())
            .select_from(Case)
            .outerjoin(RootCause, RootCause.case_id == Case.id)
            .where(RootCause.id.is_(None))
        )
        or 0
    )

    in_test = db.execute(select(Status.id).where(Status.key == "IN_TEST")).scalar_one_or_none()
    cases_in_test = 0
    if in_test:
        cases_in_test = db.scalar(select(func.count()).select_from(Case).where(Case.status_id == in_test)) or 0

    open_reg = db.scalar(
        select(func.count()).select_from(RegressionRun).where(RegressionRun.result.in_(["open", "partial"]))
    ) or 0

    return EngineeringDashboard(
        new_cases=int(new_cases),
        critical_cases=int(critical_cases),
        unassigned_cases=int(unassigned),
        cases_without_root_cause=cases_without_root_cause,
        cases_in_test=int(cases_in_test),
        open_regressions=int(open_reg),
        system_builds=_build_statuses(db),
    )


@router.get("/admin", response_model=AdminDashboard)
def dash_admin(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN))],
) -> AdminDashboard:
    active_users = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True), User.deleted_at.is_(None))) or 0

    closed_st = db.execute(select(Status.id).where(Status.key.in_(["CLOSED", "REJECTED"]))).scalars().all()
    closed_ids = list(closed_st)
    if closed_ids:
        open_cases = db.scalar(select(func.count()).select_from(Case).where(Case.status_id.not_in(closed_ids))) or 0
    else:
        open_cases = db.scalar(select(func.count()).select_from(Case)) or 0

    # Top error categories from root causes
    rows = db.execute(
        select(ErrorCategory.name, func.count())
        .join(RootCause, RootCause.error_category_id == ErrorCategory.id)
        .group_by(ErrorCategory.name)
        .order_by(func.count().desc())
        .limit(8)
    ).all()
    top_cats = [LabelCount(label=r[0], count=int(r[1])) for r in rows]

    prod_posts = db.execute(
        select(PostProcessorVersion).where(PostProcessorVersion.is_productive.is_(True), PostProcessorVersion.deleted_at.is_(None))
    ).scalars().all()
    productive = [
        {"id": p.id, "name": p.name, "version": p.version, "machine_family": p.machine_family} for p in prod_posts
    ]

    mrows = db.execute(
        select(Machine.name, func.count())
        .join(Case, Case.machine_id == Machine.id)
        .where(Machine.deleted_at.is_(None))
        .group_by(Machine.name)
        .order_by(func.count().desc())
        .limit(12)
    ).all()
    per_machine = [LabelCount(label=r[0], count=int(r[1])) for r in mrows]

    srows = db.execute(
        select(Status.name, func.count()).join(Case, Case.status_id == Status.id).group_by(Status.name).order_by(func.count().desc())
    ).all()
    per_status = [LabelCount(label=r[0], count=int(r[1])) for r in srows]

    return AdminDashboard(
        active_users=int(active_users),
        open_cases=int(open_cases),
        top_error_categories=top_cats,
        productive_post_versions=productive,
        cases_per_machine=per_machine,
        cases_per_status=per_status,
        system_builds=_build_statuses(db),
    )
