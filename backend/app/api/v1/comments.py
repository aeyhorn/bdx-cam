from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core import roles as R
from app.models import Case, Comment, User
from app.schemas.comment import CommentCreate, CommentOut
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable, ensure_case_writable_production

router = APIRouter(prefix="/cases/{case_id}/comments", tags=["comments"])


@router.get("", response_model=list[CommentOut])
def list_comments(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Comment]:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    stmt = select(Comment).options(joinedload(Comment.author)).where(Comment.case_id == case_id)
    if not R.can_internal_comment(user.role.key):
        stmt = stmt.where(Comment.comment_type != "INTERNAL")
    stmt = stmt.order_by(Comment.created_at.asc())
    rows = db.execute(stmt).scalars().all()
    out: list[Comment] = []
    for row in rows:
        out.append(row)
    return out


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    case_id: int,
    body: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Comment:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    if body.comment_type == "INTERNAL" and not R.can_internal_comment(user.role.key):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Internal comments not allowed")
    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot comment")
    co = Comment(case_id=case_id, author_id=user.id, comment_type=body.comment_type, text=body.text)
    db.add(co)
    db.flush()
    log_action(
        db,
        entity_type="Comment",
        entity_id=co.id,
        action="created",
        performed_by=user.id,
        new_value={"case_id": case_id, "type": body.comment_type},
        case_id=case_id,
    )
    db.commit()
    return db.execute(select(Comment).options(joinedload(Comment.author)).where(Comment.id == co.id)).scalar_one()
