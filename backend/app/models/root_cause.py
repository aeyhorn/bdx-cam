from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RootCause(Base):
    __tablename__ = "root_causes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), unique=True)
    error_category_id: Mapped[int | None] = mapped_column(ForeignKey("error_categories.id"), nullable=True)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    cps_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    nc_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    case: Mapped["Case"] = relationship(back_populates="root_cause")
    error_category: Mapped["ErrorCategory | None"] = relationship()
    creator: Mapped["User"] = relationship()
