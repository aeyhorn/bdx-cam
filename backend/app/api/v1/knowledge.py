from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.models import KnowledgeEntry, User
from app.schemas.knowledge import KnowledgeEntryCreate, KnowledgeEntryOut, KnowledgeEntryUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeEntryOut])
def list_knowledge(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[KnowledgeEntry]:
    rows = db.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.updated_at.desc())).scalars().all()
    return list(rows)


@router.get("/{kid}", response_model=KnowledgeEntryOut)
def get_knowledge(
    kid: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> KnowledgeEntry:
    ke = db.get(KnowledgeEntry, kid)
    if ke is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return ke


@router.delete("/{kid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    kid: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    ke = db.get(KnowledgeEntry, kid)
    if ke is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    log_action(
        db,
        entity_type="KnowledgeEntry",
        entity_id=kid,
        action="deleted",
        performed_by=user.id,
        old_value={"title": ke.title},
    )
    db.delete(ke)
    db.commit()


@router.post("", response_model=KnowledgeEntryOut, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    body: KnowledgeEntryCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> KnowledgeEntry:
    ke = KnowledgeEntry(**body.model_dump(), created_by=user.id)
    db.add(ke)
    db.flush()
    log_action(
        db,
        entity_type="KnowledgeEntry",
        entity_id=ke.id,
        action="created",
        performed_by=user.id,
        new_value={"title": ke.title},
    )
    db.commit()
    db.refresh(ke)
    return ke


@router.patch("/{kid}", response_model=KnowledgeEntryOut)
def patch_knowledge(
    kid: int,
    body: KnowledgeEntryUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> KnowledgeEntry:
    ke = db.get(KnowledgeEntry, kid)
    if ke is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ke, k, v)
    ke.updated_by = user.id
    log_action(
        db,
        entity_type="KnowledgeEntry",
        entity_id=ke.id,
        action="updated",
        performed_by=user.id,
        new_value=body.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(ke)
    return ke
