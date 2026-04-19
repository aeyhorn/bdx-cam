from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"))
    control_system_id: Mapped[int | None] = mapped_column(ForeignKey("control_systems.id"), nullable=True)
    post_processor_version_id: Mapped[int] = mapped_column(ForeignKey("post_processor_versions.id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    part_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nc_program_name: Mapped[str] = mapped_column(String(512))
    nc_line_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity_id: Mapped[int] = mapped_column(ForeignKey("severities.id"))
    priority_id: Mapped[int] = mapped_column(ForeignKey("priorities.id"))
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    machine: Mapped["Machine"] = relationship(foreign_keys=[machine_id])
    control_system: Mapped["ControlSystem | None"] = relationship(foreign_keys=[control_system_id])
    post_processor_version: Mapped["PostProcessorVersion"] = relationship()
    reporter: Mapped["User"] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    severity: Mapped["Severity"] = relationship()
    priority: Mapped["Priority"] = relationship()
    status: Mapped["Status"] = relationship()

    attachments: Mapped[list["CaseAttachment"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    root_cause: Mapped["RootCause | None"] = relationship(
        back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    test_case_links: Mapped[list["CaseTestCase"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
