from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ControlSystemOut(ORMModel):
    id: int
    name: str
    version: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ControlSystemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str | None = None
    notes: str | None = None


class ControlSystemUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    notes: str | None = None


class MachineOut(ORMModel):
    id: int
    name: str
    manufacturer: str | None
    model: str | None
    control_system_id: int | None
    location: str | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    control_system: ControlSystemOut | None = None


class MachineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    manufacturer: str | None = None
    model: str | None = None
    control_system_id: int | None = None
    location: str | None = None
    is_active: bool = True
    notes: str | None = None


class MachineUpdate(BaseModel):
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    control_system_id: int | None = None
    location: str | None = None
    is_active: bool | None = None
    notes: str | None = None
