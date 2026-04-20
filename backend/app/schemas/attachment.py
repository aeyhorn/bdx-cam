from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AttachmentOut(ORMModel):
    id: int
    case_id: int
    file_name: str
    file_type: str | None
    attachment_role: str
    linked_project_name: str | None
    notes: str | None
    uploaded_by: int
    created_at: datetime


class AttachmentUploadResponse(AttachmentOut):
    download_url: str


class AttachmentUpdate(BaseModel):
    attachment_role: str | None = None
    linked_project_name: str | None = None
    notes: str | None = None


class AttachmentTextOut(BaseModel):
    attachment_id: int
    file_name: str
    content: str


class AttachmentTextUpdate(BaseModel):
    content: str
