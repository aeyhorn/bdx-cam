from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ChangeRequest, TicketCounter


def next_ticket_no(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    counter = db.get(TicketCounter, year)
    if counter is None:
        counter = TicketCounter(year=year, last_value=0)
        db.add(counter)
        db.flush()
    counter.last_value += 1
    db.flush()
    return f"CAM-{year}-{counter.last_value:05d}"


def next_change_no(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"CR-{year}-"
    n = db.scalar(
        select(func.count()).select_from(ChangeRequest).where(ChangeRequest.change_no.like(f"{prefix}%"))
    )
    n = int(n or 0)
    return f"{prefix}{n + 1:05d}"
