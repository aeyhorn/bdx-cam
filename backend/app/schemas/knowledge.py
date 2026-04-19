from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class KnowledgeEntryOut(ORMModel):
    id: int
    title: str
    symptom: str | None
    cause: str | None
    resolution: str | None
    error_category_id: int | None
    created_by: int
    updated_by: int | None
    created_at: datetime
    updated_at: datetime


class KnowledgeEntryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    symptom: str | None = None
    cause: str | None = None
    resolution: str | None = None
    error_category_id: int | None = None


class KnowledgeEntryUpdate(BaseModel):
    title: str | None = None
    symptom: str | None = None
    cause: str | None = None
    resolution: str | None = None
    error_category_id: int | None = None
