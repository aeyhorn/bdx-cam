from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    old_value_json: str | None
    new_value_json: str | None
    performed_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
