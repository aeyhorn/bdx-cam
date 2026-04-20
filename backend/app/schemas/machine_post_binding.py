from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.machine import ControlSystemOut, MachineOut
from app.schemas.post_version import PostProcessorVersionOut


class MachinePostBindingOut(ORMModel):
    id: int
    machine_id: int
    post_processor_version_id: int
    control_system_id: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    machine: MachineOut | None = None
    post_processor_version: PostProcessorVersionOut | None = None
    control_system: ControlSystemOut | None = None


class MachinePostBindingCreate(BaseModel):
    machine_id: int
    post_processor_version_id: int
    control_system_id: int
    notes: str | None = None


class MachinePostBindingUpdate(BaseModel):
    notes: str | None = None
