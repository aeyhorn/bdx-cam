from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RoleOut(ORMModel):
    id: int
    key: str
    name: str
    description: str | None


class SeverityOut(ORMModel):
    id: int
    key: str
    name: str
    sort_order: int


class PriorityOut(ORMModel):
    id: int
    key: str
    name: str
    sort_order: int


class StatusOut(ORMModel):
    id: int
    key: str
    name: str
    sort_order: int
    role_visibility: str | None


class StatusCreate(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sort_order: int = 0
    role_visibility: str | None = None


class StatusUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    role_visibility: str | None = None


class ErrorCategoryOut(ORMModel):
    id: int
    name: str
    description: str | None


class ErrorCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ErrorCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
