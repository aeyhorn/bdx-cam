from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AgentRunOut(ORMModel):
    id: int
    case_id: int | None
    test_case_id: int | None
    trigger_mode: str
    agent_type: str
    status: str
    input_snapshot: dict | None
    output_summary: str | None
    output_structured: dict | None
    knowledge_entry_id: int | None
    model_name: str | None
    model_version: str | None
    error_message: str | None
    started_by: int | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentRunStart(BaseModel):
    case_id: int | None = None
    test_case_id: int | None = None
    trigger_mode: str = Field(default="manual")

