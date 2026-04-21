from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PostProcessorVersionOut(ORMModel):
    id: int
    name: str
    version: str
    machine_family: str
    description: str | None
    status: str
    is_productive: bool
    release_date: date | None
    notes: str | None
    code_file_name: str | None = None
    code_file_type: str | None = None
    created_at: datetime
    updated_at: datetime


class PostProcessorVersionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=128)
    machine_family: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = "draft"
    is_productive: bool = False
    release_date: date | None = None
    notes: str | None = None


class PostProcessorVersionUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    machine_family: str | None = None
    description: str | None = None
    status: str | None = None
    is_productive: bool | None = None
    release_date: date | None = None
    notes: str | None = None
