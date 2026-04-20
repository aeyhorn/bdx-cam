from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemBuildVersion(Base):
    __tablename__ = "system_build_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    component: Mapped[str] = mapped_column(String(128), index=True)
    version_label: Mapped[str] = mapped_column(String(128))
    build_no: Mapped[int] = mapped_column(Integer)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
