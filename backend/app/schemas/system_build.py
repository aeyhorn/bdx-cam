from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SystemBuildVersionOut(ORMModel):
    id: int
    component: str
    version_label: str
    build_no: int
    changelog: str | None
    is_deployed: bool
    created_at: datetime


class SystemBuildVersionCreate(BaseModel):
    component: str = Field(min_length=1, max_length=128)
    version_label: str = Field(min_length=1, max_length=128)
    changelog: str | None = None
    is_deployed: bool = False


class SystemBuildVersionUpdate(BaseModel):
    component: str | None = Field(default=None, min_length=1, max_length=128)
    version_label: str | None = Field(default=None, min_length=1, max_length=128)
    changelog: str | None = None
    is_deployed: bool | None = None


class SystemBuildComparison(ORMModel):
    component: str
    latest_build_no: int
    latest_version_label: str
    latest_created_at: datetime
    deployed_build_no: int | None
    deployed_version_label: str | None
    deployed_created_at: datetime | None
    is_outdated: bool
