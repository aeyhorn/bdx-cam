from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RootCauseOut(ORMModel):
    id: int
    case_id: int
    error_category_id: int | None
    hypothesis: str | None
    confirmed: bool
    cps_reference: str | None
    nc_pattern: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class RootCauseCreate(BaseModel):
    error_category_id: int | None = None
    hypothesis: str | None = None
    confirmed: bool = False
    cps_reference: str | None = None
    nc_pattern: str | None = None


class RootCauseUpdate(BaseModel):
    error_category_id: int | None = None
    hypothesis: str | None = None
    confirmed: bool | None = None
    cps_reference: str | None = None
    nc_pattern: str | None = None
