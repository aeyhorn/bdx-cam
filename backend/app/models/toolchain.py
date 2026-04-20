from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CamStepModel(Base):
    """CAM / step program identity (e.g. part + manufacturing revision)."""

    __tablename__ = "cam_step_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MachinePostBinding(Base):
    """Approved shop-floor tuple: machine · control system · post processor version."""

    __tablename__ = "machine_post_bindings"
    __table_args__ = (
        UniqueConstraint(
            "machine_id",
            "post_processor_version_id",
            "control_system_id",
            name="uq_machine_post_control",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"))
    post_processor_version_id: Mapped[int] = mapped_column(ForeignKey("post_processor_versions.id"))
    control_system_id: Mapped[int] = mapped_column(ForeignKey("control_systems.id"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    machine: Mapped["Machine"] = relationship()
    post_processor_version: Mapped["PostProcessorVersion"] = relationship()
    control_system: Mapped["ControlSystem"] = relationship()
