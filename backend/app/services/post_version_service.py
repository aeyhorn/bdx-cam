from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import PostProcessorVersion


def enforce_single_productive_per_family(db: Session, family: str, exclude_id: int | None = None) -> None:
    """Only one productive post version per machine_family."""
    q = update(PostProcessorVersion).where(
        PostProcessorVersion.machine_family == family,
        PostProcessorVersion.deleted_at.is_(None),
        PostProcessorVersion.is_productive.is_(True),
    )
    if exclude_id is not None:
        q = q.where(PostProcessorVersion.id != exclude_id)
    db.execute(q.values(is_productive=False))
    db.flush()
