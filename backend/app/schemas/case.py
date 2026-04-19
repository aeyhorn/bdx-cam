from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.lookup import PriorityOut, SeverityOut, StatusOut
from app.schemas.machine import ControlSystemOut, MachineOut
from app.schemas.post_version import PostProcessorVersionOut
class CaseBriefUser(ORMModel):
    id: int
    first_name: str
    last_name: str
    email: str


class CaseOut(ORMModel):
    id: int
    ticket_no: str
    title: str
    description: str | None
    machine_id: int
    control_system_id: int | None
    post_processor_version_id: int
    reporter_id: int
    assignee_id: int | None
    project_name: str | None
    part_name: str | None
    nc_program_name: str
    nc_line_reference: str | None
    expected_behavior: str | None
    actual_behavior: str | None
    severity_id: int
    priority_id: int
    status_id: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    machine: MachineOut | None = None
    control_system: ControlSystemOut | None = None
    post_processor_version: PostProcessorVersionOut | None = None
    reporter: CaseBriefUser | None = None
    assignee: CaseBriefUser | None = None
    severity: SeverityOut | None = None
    priority: PriorityOut | None = None
    status: StatusOut | None = None


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    machine_id: int
    post_processor_version_id: int
    nc_program_name: str = Field(min_length=1, max_length=512)
    severity_id: int
    control_system_id: int | None = None
    project_name: str | None = None
    part_name: str | None = None
    nc_line_reference: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None


class CaseUpdateProduction(BaseModel):
    """Fields production may edit on own cases."""
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = None
    project_name: str | None = None
    part_name: str | None = None
    nc_line_reference: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None


class CasePatch(BaseModel):
    """PATCH body; allowed fields depend on role (enforced in API)."""

    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = None
    machine_id: int | None = None
    control_system_id: int | None = None
    post_processor_version_id: int | None = None
    assignee_id: int | None = None
    project_name: str | None = None
    part_name: str | None = None
    nc_program_name: str | None = None
    nc_line_reference: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    severity_id: int | None = None
    priority_id: int | None = None
    status_id: int | None = None
    closed_at: datetime | None = None


class CaseUpdateEngineering(BaseModel):
    title: str | None = None
    description: str | None = None
    machine_id: int | None = None
    control_system_id: int | None = None
    post_processor_version_id: int | None = None
    assignee_id: int | None = None
    project_name: str | None = None
    part_name: str | None = None
    nc_program_name: str | None = None
    nc_line_reference: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    severity_id: int | None = None
    priority_id: int | None = None
    status_id: int | None = None
    closed_at: datetime | None = None
