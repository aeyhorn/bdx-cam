"""Seed roles, lookups, categories, and initial admin. Run: python -m scripts.seed from backend directory."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    ControlSystem,
    ErrorCategory,
    Machine,
    MachinePostBinding,
    PostProcessorVersion,
    Priority,
    Role,
    Severity,
    Status,
    SystemBuildVersion,
    User,
)


def seed(session: Session) -> None:
    settings = get_settings()

    roles_data = [
        ("ADMIN", "Administrator", "Full system access"),
        ("FEEDBACK_PRODUCTION", "Production Feedback", "Shopfloor reporting"),
        ("ENGINEERING", "Engineering", "Analysis and change"),
    ]
    for key, name, desc in roles_data:
        if session.execute(select(Role.id).where(Role.key == key)).scalar_one_or_none() is None:
            session.add(Role(key=key, name=name, description=desc))
    session.flush()

    sev = [
        ("LOW", "Low", 10),
        ("MEDIUM", "Medium", 20),
        ("HIGH", "High", 30),
        ("CRITICAL", "Critical", 40),
    ]
    for key, name, so in sev:
        if session.execute(select(Severity.id).where(Severity.key == key)).scalar_one_or_none() is None:
            session.add(Severity(key=key, name=name, sort_order=so))

    pri = [
        ("LOW", "Low", 10),
        ("NORMAL", "Normal", 20),
        ("HIGH", "High", 30),
        ("URGENT", "Urgent", 40),
    ]
    for key, name, so in pri:
        if session.execute(select(Priority.id).where(Priority.key == key)).scalar_one_or_none() is None:
            session.add(Priority(key=key, name=name, sort_order=so))

    stat = [
        ("NEW", "New", 10, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("IN_REVIEW", "In review", 20, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("FEEDBACK_REQUESTED", "Feedback requested", 30, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("TECHNICALLY_ANALYZED", "Technically analyzed", 40, '["ADMIN","ENGINEERING"]'),
        ("CHANGE_REQUESTED", "Change requested", 50, '["ADMIN","ENGINEERING"]'),
        ("IN_IMPLEMENTATION", "In implementation", 60, '["ADMIN","ENGINEERING"]'),
        ("IN_TEST", "In test", 70, '["ADMIN","ENGINEERING"]'),
        ("RETEST_PRODUCTION", "Retest production", 80, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("APPROVED", "Approved", 90, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("CLOSED", "Closed", 100, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
        ("REJECTED", "Rejected", 110, '["ADMIN","ENGINEERING","FEEDBACK_PRODUCTION"]'),
    ]
    for key, name, so, vis in stat:
        if session.execute(select(Status.id).where(Status.key == key)).scalar_one_or_none() is None:
            session.add(Status(key=key, name=name, sort_order=so, role_visibility=vis))

    cats = [
        "Syntax / Steuerungsproblem",
        "Achslogik",
        "Haupt-/Gegenspindel",
        "B-Achse",
        "Werkzeugwechsel",
        "Zyklusproblem",
        "Sicherheitsrisiko",
        "Lynette / Sonderfunktion",
        "Format / Stil",
        "Shopfloor-Unpraktikabilität",
    ]
    for name in cats:
        if session.execute(select(ErrorCategory.id).where(ErrorCategory.name == name)).scalar_one_or_none() is None:
            session.add(ErrorCategory(name=name))

    session.flush()

    admin_role = session.execute(select(Role).where(Role.key == "ADMIN")).scalar_one()
    if session.execute(select(User.id).where(User.email == settings.INITIAL_ADMIN_EMAIL)).scalar_one_or_none() is None:
        session.add(
            User(
                first_name="Admin",
                last_name="User",
                email=settings.INITIAL_ADMIN_EMAIL,
                password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                role_id=admin_role.id,
                is_active=True,
            )
        )

    # Demo post version for development
    if session.execute(select(PostProcessorVersion.id).where(PostProcessorVersion.name == "Demo Post")).scalar_one_or_none() is None:
        session.add(
            PostProcessorVersion(
                name="Demo Post",
                version="1.0.0",
                machine_family="GENERIC",
                description="Seeded demo post processor",
                status="released",
                is_productive=True,
            )
        )

    if session.execute(select(ControlSystem.id).where(ControlSystem.name == "Demo Control")).scalar_one_or_none() is None:
        session.add(ControlSystem(name="Demo Control", version="1.0", notes="Seed"))

    session.flush()

    cs_demo = session.execute(select(ControlSystem).where(ControlSystem.name == "Demo Control")).scalar_one()
    if session.execute(select(Machine.id).where(Machine.name == "Demo Machine")).scalar_one_or_none() is None:
        session.add(
            Machine(
                name="Demo Machine",
                manufacturer="Demo",
                model="DM-1",
                control_system_id=cs_demo.id,
                location="Hall 1",
                is_active=True,
            )
        )

    session.flush()
    demo_pp = session.execute(select(PostProcessorVersion).where(PostProcessorVersion.name == "Demo Post")).scalar_one_or_none()
    demo_m = session.execute(select(Machine).where(Machine.name == "Demo Machine")).scalar_one_or_none()
    if demo_pp is not None and demo_m is not None:
        dup = session.execute(
            select(MachinePostBinding.id).where(
                MachinePostBinding.machine_id == demo_m.id,
                MachinePostBinding.post_processor_version_id == demo_pp.id,
                MachinePostBinding.control_system_id == cs_demo.id,
            )
        ).scalar_one_or_none()
        if dup is None:
            session.add(
                MachinePostBinding(
                    machine_id=demo_m.id,
                    post_processor_version_id=demo_pp.id,
                    control_system_id=cs_demo.id,
                    notes="Seed: Demo-Fertigungsbindung",
                )
            )

    build_seeds = [
        ("backend-api", "1.0.0", "Initial API baseline", True),
        ("frontend-web", "1.0.0", "Initial UI baseline", True),
        ("post-library", "1.0.0", "Initial productive post package", True),
    ]
    for comp, ver, note, deployed in build_seeds:
        exists = session.execute(
            select(SystemBuildVersion.id).where(
                SystemBuildVersion.component == comp,
                SystemBuildVersion.version_label == ver,
            ).limit(1)
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                SystemBuildVersion(
                    component=comp,
                    version_label=ver,
                    build_no=1,
                    changelog=note,
                    is_deployed=deployed,
                )
            )

    session.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
        print("Seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
