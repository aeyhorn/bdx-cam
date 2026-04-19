from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ChangeRequestOut(ORMModel):
    id: int
    change_no: str
    title: str
    description: str | None
    status: str
    owner_id: int | None
    post_processor_version_id: int | None
    cps_reference: str | None
    target_behavior: str | None
    technical_solution: str | None
    risk_notes: str | None
    created_at: datetime
    updated_at: datetime


class ChangeRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    status: str = "open"
    owner_id: int | None = None
    post_processor_version_id: int | None = None
    cps_reference: str | None = None
    target_behavior: str | None = None
    technical_solution: str | None = None
    risk_notes: str | None = None


class ChangeRequestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    owner_id: int | None = None
    post_processor_version_id: int | None = None
    cps_reference: str | None = None
    target_behavior: str | None = None
    technical_solution: str | None = None
    risk_notes: str | None = None
