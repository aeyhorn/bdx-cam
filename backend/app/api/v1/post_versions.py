from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.roles import ADMIN
from app.models import PostProcessorVersion, User
from app.schemas.post_version import PostProcessorVersionCreate, PostProcessorVersionOut, PostProcessorVersionUpdate
from app.services.audit_service import log_action
from app.services.post_version_service import enforce_single_productive_per_family

router = APIRouter(prefix="/post-versions", tags=["post-versions"])


@router.get("", response_model=list[PostProcessorVersionOut])
def list_post_versions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[PostProcessorVersion]:
    rows = (
        db.execute(
            select(PostProcessorVersion)
            .where(PostProcessorVersion.deleted_at.is_(None))
            .order_by(PostProcessorVersion.machine_family, PostProcessorVersion.version)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.post("", response_model=PostProcessorVersionOut, status_code=status.HTTP_201_CREATED)
def create_pv(
    body: PostProcessorVersionCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> PostProcessorVersion:
    p = PostProcessorVersion(**body.model_dump())
    db.add(p)
    db.flush()
    if p.is_productive:
        enforce_single_productive_per_family(db, p.machine_family, exclude_id=p.id)
    log_action(
        db,
        entity_type="PostProcessorVersion",
        entity_id=p.id,
        action="created",
        performed_by=actor.id,
        new_value={"name": p.name, "is_productive": p.is_productive, "machine_family": p.machine_family},
    )
    db.commit()
    db.refresh(p)
    return p


@router.get("/{pv_id}", response_model=PostProcessorVersionOut)
def get_pv(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> PostProcessorVersion:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return p


@router.patch("/{pv_id}", response_model=PostProcessorVersionOut)
def update_pv(
    pv_id: int,
    body: PostProcessorVersionUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> PostProcessorVersion:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old_prod = p.is_productive
    old_family = p.machine_family
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    family = p.machine_family
    if p.is_productive:
        enforce_single_productive_per_family(db, family, exclude_id=p.id)
    if old_prod != p.is_productive or old_family != family:
        log_action(
            db,
            entity_type="PostProcessorVersion",
            entity_id=p.id,
            action="productive_changed",
            performed_by=actor.id,
            old_value={"is_productive": old_prod, "machine_family": old_family},
            new_value={"is_productive": p.is_productive, "machine_family": p.machine_family},
        )
    else:
        log_action(
            db,
            entity_type="PostProcessorVersion",
            entity_id=p.id,
            action="updated",
            performed_by=actor.id,
            old_value=old_prod,
            new_value=data,
        )
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{pv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pv(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> None:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    p.deleted_at = datetime.now(timezone.utc)
    log_action(db, entity_type="PostProcessorVersion", entity_id=p.id, action="deleted", performed_by=actor.id, old_value={"name": p.name})
    db.commit()
