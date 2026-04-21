import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core import roles as R
from app.models import Case, CaseAttachment, User
from app.schemas.attachment import (
    AttachmentOut,
    AttachmentTextOut,
    AttachmentTextUpdate,
    AttachmentUpdate,
    AttachmentUploadResponse,
)
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable, ensure_case_writable_production
from app.services.step_viewer import ensure_step_glb
from app.services.text_files import is_text_content

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
    attachment_role: str = Form("other"),
    link_to_project: bool = Form(False),
    linked_project_name: str | None = Form(None),
    notes: str | None = Form(None),
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
    role = (attachment_role or "other").strip().lower()
    if role not in ("other", "post", "generated_program"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid attachment role")
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
        attachment_role=role,
        linked_project_name=(
            (linked_project_name.strip() if linked_project_name else None)
            or (c.project_name if link_to_project else None)
        ),
        notes=notes.strip() if notes else None,
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
        new_value={
            "case_id": case_id,
            "file_name": att.file_name,
            "attachment_role": att.attachment_role,
            "linked_project_name": att.linked_project_name,
        },
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


@router.patch("/attachments/{attachment_id}", response_model=AttachmentOut)
def update_attachment(
    attachment_id: int,
    body: AttachmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CaseAttachment:
    att = db.get(CaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, att.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot update")
    data = body.model_dump(exclude_unset=True)
    if "attachment_role" in data and data["attachment_role"] is not None:
        role = str(data["attachment_role"]).strip().lower()
        if role not in ("other", "post", "generated_program"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid attachment role")
        att.attachment_role = role
    if "linked_project_name" in data:
        v = data["linked_project_name"]
        att.linked_project_name = v.strip() if isinstance(v, str) and v.strip() else None
    if "notes" in data:
        v = data["notes"]
        att.notes = v.strip() if isinstance(v, str) and v.strip() else None
    log_action(
        db,
        entity_type="Attachment",
        entity_id=att.id,
        action="updated",
        performed_by=user.id,
        new_value=data,
        case_id=att.case_id,
    )
    db.commit()
    db.refresh(att)
    return att


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


@router.get("/attachments/{attachment_id}/viewer-model")
def download_attachment_viewer_model(
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
    model_path = ensure_step_glb(att)
    return FileResponse(model_path, filename=f"{Path(att.file_name).stem}.glb", media_type="model/gltf-binary")


def _is_text_file(att: CaseAttachment) -> bool:
    return is_text_content(att.file_name, att.file_type)


@router.get("/attachments/{attachment_id}/text", response_model=AttachmentTextOut)
def read_attachment_text(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AttachmentTextOut:
    att = db.get(CaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, att.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    if not _is_text_file(att):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Attachment is not a text file")
    path = Path(att.storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text file too large for inline editor")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")
    return AttachmentTextOut(attachment_id=att.id, file_name=att.file_name, content=content)


@router.patch("/attachments/{attachment_id}/text", response_model=AttachmentTextOut)
def update_attachment_text(
    attachment_id: int,
    body: AttachmentTextUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AttachmentTextOut:
    att = db.get(CaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    c = db.get(Case, att.case_id)
    assert c is not None
    ensure_case_readable(user, c)
    if user.role.key == R.FEEDBACK_PRODUCTION:
        ensure_case_writable_production(user, c)
    elif user.role.key not in (R.ENGINEERING, R.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot edit text")
    if not _is_text_file(att):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Attachment is not a text file")
    path = Path(att.storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    payload = body.content.encode("utf-8")
    if len(payload) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text file too large for inline editor")
    path.write_bytes(payload)
    log_action(
        db,
        entity_type="Attachment",
        entity_id=att.id,
        action="text_updated",
        performed_by=user.id,
        new_value={"file_name": att.file_name, "bytes": len(payload)},
        case_id=att.case_id,
    )
    db.commit()
    return AttachmentTextOut(attachment_id=att.id, file_name=att.file_name, content=body.content)
