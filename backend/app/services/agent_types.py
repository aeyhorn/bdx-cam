from pydantic import BaseModel, Field


class RunPayload(BaseModel):
    case_id: int | None = None
    test_case_id: int | None = None
    ticket_no: str | None = None
    title: str | None = None
    description: str | None = None
    trigger_mode: str = "manual"
    context: dict = Field(default_factory=dict)


class ProposedChange(BaseModel):
    target: str
    action: str
    rationale: str


class RunResult(BaseModel):
    output_summary: str
    output_structured: dict
    knowledge_title: str
    knowledge_symptom: str | None = None
    knowledge_cause: str | None = None
    knowledge_resolution: str | None = None
    model_name: str | None = None
    model_version: str | None = None

