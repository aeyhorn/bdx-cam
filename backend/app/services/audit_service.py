import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: str,
    performed_by: int | None,
    old_value: Any = None,
    new_value: Any = None,
    case_id: int | None = None,
) -> AuditLog:
    def dumps(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        try:
            return json.dumps(v, default=str)
        except TypeError:
            return str(v)

    row = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value_json=dumps(old_value),
        new_value_json=dumps(new_value),
        performed_by=performed_by,
        case_id=case_id,
    )
    db.add(row)
    return row
