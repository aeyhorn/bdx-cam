from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TestCaseOut(ORMModel):
    id: int
    title: str
    description: str | None
    machine_id: int | None
    control_system_id: int | None
    scenario_type: str | None
    expected_result: str | None
    risk_level: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TestCaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    machine_id: int | None = None
    control_system_id: int | None = None
    scenario_type: str | None = None
    expected_result: str | None = None
    risk_level: str | None = None
    is_active: bool = True


class TestCaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    machine_id: int | None = None
    control_system_id: int | None = None
    scenario_type: str | None = None
    expected_result: str | None = None
    risk_level: str | None = None
    is_active: bool | None = None


class RegressionRunOut(ORMModel):
    id: int
    test_case_id: int
    post_processor_version_id: int
    result: str
    notes: str | None
    executed_by: int | None
    executed_at: datetime | None


class RegressionRunCreate(BaseModel):
    test_case_id: int
    post_processor_version_id: int
    result: str = Field(pattern="^(passed|failed|partial|open)$")
    notes: str | None = None
    executed_at: datetime | None = None
