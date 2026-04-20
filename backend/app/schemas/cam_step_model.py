from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CamStepModelOut(ORMModel):
    id: int
    code: str
    name: str
    revision: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CamStepModelCreate(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=512)
    revision: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class CamStepModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=512)
    revision: str | None = None
    notes: str | None = None
