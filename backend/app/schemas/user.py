from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class RoleBrief(ORMModel):
    id: int
    key: str
    name: str


class UserBrief(ORMModel):
    """Minimal user info for pickers (assignee, etc.)."""

    id: int
    first_name: str
    last_name: str
    email: str


class UserOut(ORMModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: RoleBrief | None = None


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_id: int


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role_id: int | None = None
    is_active: bool | None = None


class MeOut(UserOut):
    pass
