from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    change_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="open")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    post_processor_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("post_processor_versions.id"), nullable=True
    )
    cps_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User | None"] = relationship(foreign_keys=[owner_id])
    post_processor_version: Mapped["PostProcessorVersion | None"] = relationship()
    case_links: Mapped[list["ChangeRequestCase"]] = relationship(
        back_populates="change_request", cascade="all, delete-orphan"
    )


class ChangeRequestCase(Base):
    __tablename__ = "change_request_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    change_request_id: Mapped[int] = mapped_column(ForeignKey("change_requests.id", ondelete="CASCADE"))
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))

    change_request: Mapped["ChangeRequest"] = relationship(back_populates="case_links")
    case: Mapped["Case"] = relationship()
