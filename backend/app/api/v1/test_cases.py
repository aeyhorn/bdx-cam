import csv
import io
import json
import uuid
import zipfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.core import roles as R
from app.core.config import get_settings
from app.models import Case, CaseTestCase, TestCase, TestCaseAttachment, User
from app.schemas.test_case import (
    TestCaseAttachmentOut,
    TestCaseCreate,
    TestCaseDetailOut,
    TestCaseImportResult,
    TestCaseImportRow,
    TestCaseOut,
    TestCaseUpdate,
)
from app.services.audit_service import log_action
from app.services.case_access import ensure_case_readable
from app.services.text_files import is_text_content

router = APIRouter(tags=["test-cases"])
def _tc_upload_dir(test_case_id: int) -> Path:
    settings = get_settings()
    base = Path(settings.UPLOAD_DIR) / "test-cases" / str(test_case_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _parse_import_rows(filename: str, content: bytes) -> list[TestCaseImportRow]:
    ext = Path(filename).suffix.lower()
    if ext == ".json":
        raw = io.StringIO(content.decode("utf-8"))
        data = json.load(raw)
        return [TestCaseImportRow.model_validate(x) for x in data]
    if ext == ".csv":
        text = content.decode("utf-8")
        # supports ; and ,
        dialect = csv.Sniffer().sniff(text.splitlines()[0] + "\n")
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        return [TestCaseImportRow.model_validate(r) for r in reader]
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Only .json or .csv imports are supported")


@router.post("/test-cases/import", response_model=TestCaseImportResult)
async def import_test_cases(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
    file: UploadFile = File(...),
    programs_zip: UploadFile | None = File(default=None),
    machine_id: str | None = Form(default=None),
    control_system_id: str | None = Form(default=None),
    linked_project_name: str | None = Form(default=None),
) -> TestCaseImportResult:
    def parse_optional_int(name: str, raw: str | None) -> int | None:
        if raw is None:
            return None
        v = raw.strip()
        if v == "":
            return None
        try:
            return int(v)
        except ValueError as ex:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"{name} muss eine Zahl sein") from ex

    machine_id_i = parse_optional_int("machine_id", machine_id)
    control_system_id_i = parse_optional_int("control_system_id", control_system_id)

    src_name = file.filename or "import.json"
    rows = _parse_import_rows(src_name, await file.read())
    created = 0
    skipped = 0
    errors: list[str] = []
    attached_programs = 0
    by_program_name: dict[str, TestCase] = {}
    by_test_id: dict[str, TestCase] = {}

    existing = db.execute(select(TestCase)).scalars().all()
    dedup = {(x.scenario_type or "").strip().upper(): (x.title or "").strip().lower() for x in existing}
    dedup_set = {(k, v) for k, v in dedup.items()}

    for i, row in enumerate(rows, start=1):
        key_left = (row.test_id or "").strip().upper()
        key_right = row.title.strip().lower()
        if (key_left, key_right) in dedup_set:
            skipped += 1
            continue
        desc_parts = [
            f"Programm: {row.program_name}" if row.program_name else "",
            f"Ziel: {row.goal}" if row.goal else "",
            f"Post-Bereich: {row.affected_post_area}" if row.affected_post_area else "",
            f"Hinweis: {row.notes}" if row.notes else "",
            f"Import-Status: {row.status}" if row.status else "",
        ]
        try:
            tc = TestCase(
                title=row.title.strip(),
                description="\n".join([x for x in desc_parts if x]),
                machine_id=machine_id_i,
                control_system_id=control_system_id_i,
                scenario_type=(row.test_id or None),
                expected_result=row.expected_result,
                risk_level=row.confidence or None,
                is_active=True,
            )
            db.add(tc)
            db.flush()
            created += 1
            dedup_set.add((key_left, key_right))
            if row.program_name:
                by_program_name[row.program_name.strip().lower()] = tc
            if row.test_id:
                by_test_id[row.test_id.strip().lower()] = tc
            log_action(
                db,
                entity_type="TestCase",
                entity_id=tc.id,
                action="imported",
                performed_by=user.id,
                new_value={"scenario_type": tc.scenario_type, "title": tc.title},
            )
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    if programs_zip is not None:
        zname = programs_zip.filename or ""
        if not zname.lower().endswith(".zip"):
            errors.append("programs_zip must be a .zip file")
        else:
            payload = await programs_zip.read()
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    fname = Path(info.filename).name
                    low = fname.lower()
                    target = by_program_name.get(low)
                    if target is None:
                        tid = low.split("_", 1)[0]
                        target = by_test_id.get(tid)
                    if target is None:
                        continue
                    raw = zf.read(info.filename)
                    ext = Path(fname).suffix
                    safe_name = f"{uuid.uuid4().hex}{ext}"
                    dest = _tc_upload_dir(target.id) / safe_name
                    dest.write_bytes(raw)
                    db.add(
                        TestCaseAttachment(
                            test_case_id=target.id,
                            file_name=fname,
                            file_type=None,
                            storage_path=str(dest.resolve()),
                            attachment_role="program",
                            linked_project_name=linked_project_name.strip() if linked_project_name else None,
                        )
                    )
                    attached_programs += 1

    db.commit()
    return TestCaseImportResult(
        created=created,
        skipped=skipped,
        attached_programs=attached_programs,
        errors=errors,
    )


@router.get("/test-cases/{tc_id}/attachments", response_model=list[TestCaseAttachmentOut])
def list_test_case_attachments(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[TestCaseAttachmentOut]:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    rows = (
        db.execute(select(TestCaseAttachment).where(TestCaseAttachment.test_case_id == tc_id).order_by(TestCaseAttachment.created_at.desc()))
        .scalars()
        .all()
    )
    return [
        TestCaseAttachmentOut.model_validate(a).model_copy(update={"download_url": f"/api/v1/test-case-attachments/{a.id}/download"})
        for a in rows
    ]


@router.post("/test-cases/{tc_id}/attachments", response_model=TestCaseAttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_test_case_attachment(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
    file: UploadFile = File(...),
    attachment_role: str = Form("program"),
    linked_project_name: str | None = Form(default=None),
) -> TestCaseAttachmentOut:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    role = (attachment_role or "program").strip().lower()
    if role not in ("program", "step", "other"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid attachment role")
    content = await file.read()
    ext = Path(file.filename or "file").suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = _tc_upload_dir(tc_id) / safe_name
    dest.write_bytes(content)
    att = TestCaseAttachment(
        test_case_id=tc_id,
        file_name=file.filename or safe_name,
        file_type=file.content_type,
        storage_path=str(dest.resolve()),
        attachment_role=role,
        linked_project_name=linked_project_name.strip() if linked_project_name else None,
    )
    db.add(att)
    db.flush()
    log_action(
        db,
        entity_type="TestCaseAttachment",
        entity_id=att.id,
        action="uploaded",
        performed_by=user.id,
        new_value={"test_case_id": tc_id, "file_name": att.file_name, "attachment_role": att.attachment_role},
    )
    db.commit()
    db.refresh(att)
    return TestCaseAttachmentOut.model_validate(att).model_copy(update={"download_url": f"/api/v1/test-case-attachments/{att.id}/download"})


@router.get("/test-cases", response_model=list[TestCaseOut])
def list_test_cases(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> list[TestCase]:
    rows = (
        db.execute(
            select(TestCase)
            .options(joinedload(TestCase.machine), joinedload(TestCase.control_system))
            .order_by(TestCase.id.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.get("/test-cases/{tc_id}", response_model=TestCaseOut)
def get_tc(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = (
        db.execute(
            select(TestCase)
            .options(joinedload(TestCase.machine), joinedload(TestCase.control_system))
            .where(TestCase.id == tc_id)
        )
        .scalar_one_or_none()
    )
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return tc


@router.get("/test-cases/{tc_id}/detail", response_model=TestCaseDetailOut)
def get_tc_detail(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCaseDetailOut:
    tc = (
        db.execute(
            select(TestCase)
            .options(
                joinedload(TestCase.machine),
                joinedload(TestCase.control_system),
                joinedload(TestCase.attachments),
                joinedload(TestCase.case_links),
                joinedload(TestCase.regression_runs),
            )
            .where(TestCase.id == tc_id)
        )
        .unique()
        .scalar_one_or_none()
    )
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    return TestCaseDetailOut(
        **TestCaseOut.model_validate(tc).model_dump(),
        linked_case_ids=[x.case_id for x in tc.case_links],
        regression_count=len(tc.regression_runs),
        attachments=[
            TestCaseAttachmentOut.model_validate(a).model_copy(
                update={"download_url": f"/api/v1/test-case-attachments/{a.id}/download"}
            )
            for a in tc.attachments
        ],
    )


@router.delete("/test-cases/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tc(
    tc_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    log_action(db, entity_type="TestCase", entity_id=tc_id, action="deleted", performed_by=user.id, old_value={"title": tc.title})
    db.delete(tc)
    db.commit()


@router.post("/test-cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_tc(
    body: TestCaseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = TestCase(**body.model_dump())
    db.add(tc)
    db.flush()
    log_action(
        db,
        entity_type="TestCase",
        entity_id=tc.id,
        action="created",
        performed_by=user.id,
        new_value={"title": tc.title},
    )
    db.commit()
    return (
        db.execute(
            select(TestCase).options(joinedload(TestCase.machine), joinedload(TestCase.control_system)).where(TestCase.id == tc.id)
        )
        .scalar_one()
    )


@router.patch("/test-cases/{tc_id}", response_model=TestCaseOut)
def patch_tc(
    tc_id: int,
    body: TestCaseUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> TestCase:
    tc = db.get(TestCase, tc_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(tc, k, v)
    log_action(db, entity_type="TestCase", entity_id=tc.id, action="updated", performed_by=user.id, new_value=body.model_dump(exclude_unset=True))
    db.commit()
    return (
        db.execute(
            select(TestCase).options(joinedload(TestCase.machine), joinedload(TestCase.control_system)).where(TestCase.id == tc.id)
        )
        .scalar_one()
    )


@router.get("/test-case-attachments/{attachment_id}/download")
def download_test_case_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> FileResponse:
    att = db.get(TestCaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    path = Path(att.storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    return FileResponse(path, filename=att.file_name)


@router.delete("/test-case-attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    att = db.get(TestCaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    path = Path(att.storage_path)
    file_name = att.file_name
    tc_id = att.test_case_id
    db.delete(att)
    log_action(
        db,
        entity_type="TestCaseAttachment",
        entity_id=attachment_id,
        action="deleted",
        performed_by=user.id,
        old_value={"file_name": file_name, "test_case_id": tc_id},
    )
    db.commit()
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
    return None


def _is_text_test_case_attachment(att: TestCaseAttachment) -> bool:
    return is_text_content(att.file_name, att.file_type)


@router.get("/test-case-attachments/{attachment_id}/text")
def read_test_case_attachment_text(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> dict[str, str | int]:
    att = db.get(TestCaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if not _is_text_test_case_attachment(att):
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
    return {"attachment_id": att.id, "file_name": att.file_name, "content": content}


@router.patch("/test-case-attachments/{attachment_id}/text")
def update_test_case_attachment_text(
    attachment_id: int,
    body: dict[str, str],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> dict[str, str | int]:
    att = db.get(TestCaseAttachment, attachment_id)
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if not _is_text_test_case_attachment(att):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Attachment is not a text file")
    content = body.get("content", "")
    payload = content.encode("utf-8")
    if len(payload) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text file too large for inline editor")
    path = Path(att.storage_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    path.write_bytes(payload)
    log_action(
        db,
        entity_type="TestCaseAttachment",
        entity_id=att.id,
        action="text_updated",
        performed_by=user.id,
        new_value={"file_name": att.file_name, "bytes": len(payload)},
    )
    db.commit()
    return {"attachment_id": att.id, "file_name": att.file_name, "content": content}


@router.post("/cases/{case_id}/link-test-case/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def link_test_case(
    case_id: int,
    test_case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    tc = db.get(TestCase, test_case_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Test case not found")
    exists = db.execute(
        select(CaseTestCase.id).where(
            CaseTestCase.case_id == case_id, CaseTestCase.test_case_id == test_case_id
        )
    ).scalar_one_or_none()
    if exists is not None:
        return None
    db.add(CaseTestCase(case_id=case_id, test_case_id=test_case_id))
    log_action(
        db,
        entity_type="CaseTestCase",
        entity_id=case_id,
        action="linked_test_case",
        performed_by=user.id,
        new_value={"test_case_id": test_case_id},
        case_id=case_id,
    )
    db.commit()
    return None


@router.delete("/cases/{case_id}/link-test-case/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_test_case(
    case_id: int,
    test_case_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(R.ADMIN, R.ENGINEERING))],
) -> None:
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    ensure_case_readable(user, c)
    row = db.execute(
        select(CaseTestCase).where(
            CaseTestCase.case_id == case_id, CaseTestCase.test_case_id == test_case_id
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    db.delete(row)
    log_action(
        db,
        entity_type="CaseTestCase",
        entity_id=case_id,
        action="unlinked_test_case",
        performed_by=user.id,
        new_value={"test_case_id": test_case_id},
        case_id=case_id,
    )
    db.commit()
    return None
