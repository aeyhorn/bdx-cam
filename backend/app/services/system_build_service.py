from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SystemBuildVersion


@dataclass(frozen=True)
class BuildSpec:
    component: str
    version_label: str


def parse_build_specs(raw: str) -> list[BuildSpec]:
    specs: list[BuildSpec] = []
    for chunk in raw.split(";"):
        part = chunk.strip()
        if not part or ":" not in part:
            continue
        component, version_label = part.split(":", 1)
        c = component.strip()
        v = version_label.strip()
        if c and v:
            specs.append(BuildSpec(component=c, version_label=v))
    return specs


def register_startup_builds(db: Session, specs: list[BuildSpec], *, force_increment: bool) -> None:
    for spec in specs:
        latest = db.execute(
            select(SystemBuildVersion)
            .where(SystemBuildVersion.component == spec.component)
            .order_by(SystemBuildVersion.build_no.desc(), SystemBuildVersion.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        row: SystemBuildVersion | None = None
        if latest is not None and latest.version_label == spec.version_label and not force_increment:
            row = latest
        else:
            next_build = (latest.build_no + 1) if latest is not None else 1
            row = SystemBuildVersion(
                component=spec.component,
                version_label=spec.version_label,
                build_no=next_build,
                changelog="Auto-registriert beim Service-Start",
                is_deployed=True,
            )
            db.add(row)
            db.flush()

        db.execute(
            SystemBuildVersion.__table__.update()
            .where(SystemBuildVersion.component == spec.component, SystemBuildVersion.id != row.id)
            .values(is_deployed=False)
        )
