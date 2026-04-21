from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True)
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=True, index=True)
    trigger_mode: Mapped[str] = mapped_column(String(32), default="manual")
    agent_type: Mapped[str] = mapped_column(String(64), default="error_analysis")
    status: Mapped[str] = mapped_column(String(32), default="queued")
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    knowledge_entry_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_entries.id", ondelete="SET NULL"), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    case: Mapped["Case | None"] = relationship(foreign_keys=[case_id])
    test_case: Mapped["TestCase | None"] = relationship(foreign_keys=[test_case_id])
    knowledge_entry: Mapped["KnowledgeEntry | None"] = relationship(foreign_keys=[knowledge_entry_id])
    starter: Mapped["User | None"] = relationship(foreign_keys=[started_by])

