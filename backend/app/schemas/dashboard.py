from pydantic import BaseModel


class CountItem(BaseModel):
    label: str
    value: int


class LabelCount(BaseModel):
    label: str
    count: int


class ProductionDashboard(BaseModel):
    my_open_cases: int
    open_questions: int
    recent_cases: list[dict]


class EngineeringDashboard(BaseModel):
    new_cases: int
    critical_cases: int
    unassigned_cases: int
    cases_without_root_cause: int
    cases_in_test: int
    open_regressions: int


class AdminDashboard(BaseModel):
    active_users: int
    open_cases: int
    top_error_categories: list[LabelCount]
    productive_post_versions: list[dict]
    cases_per_machine: list[LabelCount]
    cases_per_status: list[LabelCount]
