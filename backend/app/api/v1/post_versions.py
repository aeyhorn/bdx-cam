from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import get_settings
from app.core.roles import ADMIN
from app.models import PostProcessorVersion, User
from app.schemas.post_version import PostProcessorVersionCreate, PostProcessorVersionOut, PostProcessorVersionUpdate
from app.services.audit_service import log_action
from app.services.post_version_service import enforce_single_productive_per_family
from app.services.text_files import is_text_content

router = APIRouter(prefix="/post-versions", tags=["post-versions"])


def _pv_upload_dir(pv_id: int) -> Path:
    settings = get_settings()
    base = Path(settings.UPLOAD_DIR) / "post-versions" / str(pv_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


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


@router.post("/{pv_id}/code", response_model=PostProcessorVersionOut)
async def upload_pv_code(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
    file: UploadFile = File(...),
) -> PostProcessorVersion:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    content = await file.read()
    ext = Path(file.filename or "code").suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = _pv_upload_dir(p.id) / safe_name
    dest.write_bytes(content)
    p.code_file_name = file.filename or safe_name
    p.code_file_type = file.content_type
    p.code_storage_path = str(dest.resolve())
    log_action(
        db,
        entity_type="PostProcessorVersion",
        entity_id=p.id,
        action="code_uploaded",
        performed_by=actor.id,
        new_value={"code_file_name": p.code_file_name},
    )
    db.commit()
    db.refresh(p)
    return p


@router.get("/{pv_id}/code")
def download_pv_code(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if not p.code_storage_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No code file")
    path = Path(p.code_storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    return FileResponse(path, filename=p.code_file_name or path.name)


@router.delete("/{pv_id}/code", response_model=PostProcessorVersionOut)
def delete_pv_code(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> PostProcessorVersion:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    old_name = p.code_file_name
    if p.code_storage_path:
        path = Path(p.code_storage_path)
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass
    p.code_file_name = None
    p.code_file_type = None
    p.code_storage_path = None
    log_action(
        db,
        entity_type="PostProcessorVersion",
        entity_id=p.id,
        action="code_deleted",
        performed_by=actor.id,
        old_value={"code_file_name": old_name},
    )
    db.commit()
    db.refresh(p)
    return p


def _is_text_post_code(p: PostProcessorVersion) -> bool:
    if not p.code_file_name:
        return False
    return is_text_content(p.code_file_name, p.code_file_type)


@router.get("/{pv_id}/code/text")
def read_pv_code_text(
    pv_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict[str, str | int]:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if not p.code_storage_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No code file")
    if not _is_text_post_code(p):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Code file is not a text file")
    path = Path(p.code_storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text file too large for inline editor")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")
    return {"post_version_id": p.id, "file_name": p.code_file_name or path.name, "content": content}


@router.patch("/{pv_id}/code/text")
def update_pv_code_text(
    pv_id: int,
    body: dict[str, str],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_roles(ADMIN))],
) -> dict[str, str | int]:
    p = db.get(PostProcessorVersion, pv_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if not p.code_storage_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No code file")
    if not _is_text_post_code(p):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Code file is not a text file")
    content = body.get("content", "")
    payload = content.encode("utf-8")
    if len(payload) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text file too large for inline editor")
    path = Path(p.code_storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    path.write_bytes(payload)
    log_action(
        db,
        entity_type="PostProcessorVersion",
        entity_id=p.id,
        action="code_text_updated",
        performed_by=actor.id,
        new_value={"code_file_name": p.code_file_name, "bytes": len(payload)},
    )
    db.commit()
    return {"post_version_id": p.id, "file_name": p.code_file_name or path.name, "content": content}
