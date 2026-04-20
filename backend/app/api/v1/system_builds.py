from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import SystemBuildVersion, User
from app.schemas.system_build import (
    SystemBuildVersionCreate,
    SystemBuildVersionOut,
    SystemBuildVersionUpdate,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/system-builds", tags=["system-builds"])


@router.get("", response_model=list[SystemBuildVersionOut])
def list_system_builds(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[SystemBuildVersion]:
    rows = db.execute(
        select(SystemBuildVersion)
        .order_by(SystemBuildVersion.component.asc(), SystemBuildVersion.build_no.desc(), SystemBuildVersion.id.desc())
    ).scalars().all()
    return list(rows)


@router.post("", response_model=SystemBuildVersionOut, status_code=status.HTTP_201_CREATED)
def create_system_build(
    body: SystemBuildVersionCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> SystemBuildVersion:
    latest = db.execute(
        select(SystemBuildVersion)
        .where(SystemBuildVersion.component == body.component)
        .order_by(SystemBuildVersion.build_no.desc(), SystemBuildVersion.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    next_no = (latest.build_no + 1) if latest is not None else 1

    row = SystemBuildVersion(
        component=body.component.strip(),
        version_label=body.version_label.strip(),
        build_no=next_no,
        changelog=body.changelog,
        is_deployed=body.is_deployed,
    )
    db.add(row)
    db.flush()
    if row.is_deployed:
        db.execute(
            SystemBuildVersion.__table__.update()
            .where(SystemBuildVersion.component == row.component, SystemBuildVersion.id != row.id)
            .values(is_deployed=False)
        )
    log_action(
        db,
        entity_type="SystemBuildVersion",
        entity_id=row.id,
        action="created",
        performed_by=actor.id,
        new_value={"component": row.component, "version_label": row.version_label, "build_no": row.build_no},
    )
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{row_id}", response_model=SystemBuildVersionOut)
def update_system_build(
    row_id: int,
    body: SystemBuildVersionUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> SystemBuildVersion:
    row = db.get(SystemBuildVersion, row_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old = {"component": row.component, "version_label": row.version_label, "is_deployed": row.is_deployed}
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if isinstance(v, str):
            v = v.strip()
        setattr(row, k, v)
    if row.is_deployed:
        db.execute(
            SystemBuildVersion.__table__.update()
            .where(SystemBuildVersion.component == row.component, SystemBuildVersion.id != row.id)
            .values(is_deployed=False)
        )
    log_action(
        db,
        entity_type="SystemBuildVersion",
        entity_id=row.id,
        action="updated",
        performed_by=actor.id,
        old_value=old,
        new_value=data,
    )
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_build(
    row_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    row = db.get(SystemBuildVersion, row_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    log_action(
        db,
        entity_type="SystemBuildVersion",
        entity_id=row.id,
        action="deleted",
        performed_by=actor.id,
        old_value={"component": row.component, "version_label": row.version_label, "build_no": row.build_no},
    )
    db.delete(row)
    db.commit()
