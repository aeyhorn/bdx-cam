import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core import roles as R
from app.models import Case, CaseAttachment, User
from app.schemas.attachment import AttachmentOut, AttachmentUploadResponse
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable, ensure_case_writable_production

router = APIRouter(tags=["attachments"])


def _ensure_upload_dir(case_id: int) -> Path:
    settings = get_settings()
    base = Path(settings.UPLOAD_DIR) / str(case_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


@router.get("/cases/{case_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[CaseAttachment]:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    rows = db.execute(select(CaseAttachment).where(CaseAttachment.case_id == case_id).order_by(CaseAttachment.created_at.desc())).scalars().all()
    return list(rows)


@router.post("/cases/{case_id}/attachments", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> AttachmentUploadResponse:
    settings = get_settings()
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot upload")
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    ext = Path(file.filename or "file").suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = _ensure_upload_dir(case_id)
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(content)
    rel = str(dest_path.resolve())
    att = CaseAttachment(
        case_id=case_id,
        file_name=file.filename or safe_name,
        file_type=file.content_type,
        storage_path=rel,
        uploaded_by=user.id,
    )
    db.add(att)
    db.flush()
    log_action(
        db,
        entity_type="Attachment",
        entity_id=att.id,
        action="uploaded",
        performed_by=user.id,
        new_value={"case_id": case_id, "file_name": att.file_name},
        case_id=case_id,
    )
    db.commit()
    db.refresh(att)
    return AttachmentUploadResponse(
        id=att.id,
        case_id=att.case_id,
        file_name=att.file_name,
        file_type=att.file_type,
        uploaded_by=att.uploaded_by,
        created_at=att.created_at,
        download_url=f"/api/v1/attachments/{att.id}/download",
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    att = db.get(CaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, att.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot delete")
    path = att.storage_path
    fn = att.file_name
    cid = att.case_id
    db.delete(att)
    log_action(
        db,
        entity_type="Attachment",
        entity_id=attachment_id,
        action="deleted",
        performed_by=user.id,
        old_value={"file_name": fn},
        case_id=cid,
    )
    db.commit()
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    att = db.get(CaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, att.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    path = Path(att.storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    return FileResponse(path, filename=att.file_name)
