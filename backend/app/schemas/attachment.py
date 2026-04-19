from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AttachmentOut(ORMModel):
    id: int
    case_id: int
    file_name: str
    file_type: str | None
    uploaded_by: int
    created_at: datetime


class AttachmentUploadResponse(AttachmentOut):
    download_url: str
