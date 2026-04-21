import hashlib
import shlex
import subprocess
from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.attachment import CaseAttachment


def _cache_root() -> Path:
    settings = get_settings()
    root = Path(settings.STEP_VIEWER_CACHE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _is_step_file(att: CaseAttachment) -> bool:
    suffix = Path(att.file_name or "").suffix.lower()
    return suffix in {".step", ".stp"}


def _cache_key(att: CaseAttachment, src: Path) -> str:
    stat = src.stat()
    base = f"{att.id}:{stat.st_size}:{int(stat.st_mtime)}:{att.file_name}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _build_command(input_path: Path, output_path: Path) -> list[str]:
    settings = get_settings()
    template = settings.STEP_CONVERTER_COMMAND.strip()
    if not template:
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "STEP converter is not configured. Set STEP_CONVERTER_COMMAND, "
                "for example: cad-convert --input \"{input}\" --output \"{output}\""
            ),
        )
    rendered = template.format(input=str(input_path), output=str(output_path))
    return shlex.split(rendered)


def ensure_step_glb(att: CaseAttachment) -> Path:
    if not _is_step_file(att):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Attachment is not a STEP file")

    src = Path(att.storage_path)
    if not src.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")

    out = _cache_root() / f"{_cache_key(att, src)}.glb"
    if out.is_file():
        return out

    cmd = _build_command(src, out)
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start STEP converter: {exc}",
        ) from exc

    if completed.returncode != 0 or not out.is_file():
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or "Unknown converter error"
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STEP conversion failed: {detail}",
        )

    return out
