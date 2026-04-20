from pydantic import BaseModel
from datetime import datetime


class CountItem(BaseModel):
    label: str
    value: int


class LabelCount(BaseModel):
    label: str
    count: int


class SystemBuildStatus(BaseModel):
    component: str
    latest_build_no: int
    latest_version_label: str
    latest_created_at: datetime
    deployed_build_no: int | None
    deployed_version_label: str | None
    deployed_created_at: datetime | None
    is_outdated: bool


class ProductionDashboard(BaseModel):
    my_open_cases: int
    open_questions: int
    recent_cases: list[dict]
    system_builds: list[SystemBuildStatus]


class EngineeringDashboard(BaseModel):
    new_cases: int
    critical_cases: int
    unassigned_cases: int
    cases_without_root_cause: int
    cases_in_test: int
    open_regressions: int
    system_builds: list[SystemBuildStatus]


class AdminDashboard(BaseModel):
    active_users: int
    open_cases: int
    top_error_categories: list[LabelCount]
    productive_post_versions: list[dict]
    cases_per_machine: list[LabelCount]
    cases_per_status: list[LabelCount]
    system_builds: list[SystemBuildStatus]
