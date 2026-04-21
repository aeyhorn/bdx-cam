from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    machine_id: Mapped[int | None] = mapped_column(ForeignKey("machines.id"), nullable=True)
    control_system_id: Mapped[int | None] = mapped_column(ForeignKey("control_systems.id"), nullable=True)
    scenario_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    machine: Mapped["Machine | None"] = relationship()
    control_system: Mapped["ControlSystem | None"] = relationship()
    regression_runs: Mapped[list["RegressionRun"]] = relationship(back_populates="test_case")
    case_links: Mapped[list["CaseTestCase"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["TestCaseAttachment"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )


class RegressionRun(Base):
    __tablename__ = "regression_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    post_processor_version_id: Mapped[int] = mapped_column(ForeignKey("post_processor_versions.id"))
    result: Mapped[str] = mapped_column(String(32), default="open")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    test_case: Mapped["TestCase"] = relationship(back_populates="regression_runs")
    post_processor_version: Mapped["PostProcessorVersion"] = relationship()
    executor: Mapped["User | None"] = relationship()


class CaseTestCase(Base):
    __tablename__ = "case_test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))

    case: Mapped["Case"] = relationship(back_populates="test_case_links")
    test_case: Mapped["TestCase"] = relationship(back_populates="case_links")


class TestCaseAttachment(Base):
    __tablename__ = "test_case_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024))
    attachment_role: Mapped[str] = mapped_column(String(32), default="program")
    linked_project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    test_case: Mapped["TestCase"] = relationship(back_populates="attachments")
