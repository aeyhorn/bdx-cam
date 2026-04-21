from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class _RefOut(ORMModel):
    id: int
    name: str


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
    machine: _RefOut | None = None
    control_system: _RefOut | None = None


class TestCaseAttachmentOut(ORMModel):
    id: int
    test_case_id: int
    file_name: str
    file_type: str | None
    attachment_role: str
    linked_project_name: str | None
    created_at: datetime
    download_url: str | None = None


class TestCaseDetailOut(TestCaseOut):
    linked_case_ids: list[int] = []
    regression_count: int = 0
    attachments: list[TestCaseAttachmentOut] = []


class TestCaseImportRow(BaseModel):
    test_id: str | None = None
    program_name: str | None = None
    title: str
    goal: str | None = None
    expected_result: str | None = None
    affected_post_area: str | None = None
    observed_result: str | None = None
    status: str | None = None
    proposed_correction: str | None = None
    confidence: str | None = None
    notes: str | None = None


class TestCaseImportResult(BaseModel):
    created: int
    skipped: int
    attached_programs: int
    errors: list[str]


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


class RegressionRunUpdate(BaseModel):
    result: Literal["passed", "failed", "partial", "open"] | None = None
    notes: str | None = None
    executed_at: datetime | None = None
