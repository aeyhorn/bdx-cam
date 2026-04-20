from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Case, CaseAttachment, CamStepModel, Machine, MachinePostBinding


def effective_control_system_id(machine: Machine, case_control_system_id: int | None) -> int | None:
    return case_control_system_id if case_control_system_id is not None else machine.control_system_id


def require_approved_toolchain(
    db: Session,
    *,
    machine_id: int,
    post_processor_version_id: int,
    control_system_id: int | None,
) -> None:
    machine = db.get(Machine, machine_id)
    if machine is None or machine.deleted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Maschine ungültig")
    eff = effective_control_system_id(machine, control_system_id)
    if eff is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Steuerung fehlt: bitte an der Maschine hinterlegen oder beim Fall angeben.",
        )
    b = db.execute(
        select(MachinePostBinding.id)
        .where(
            MachinePostBinding.machine_id == machine_id,
            MachinePostBinding.post_processor_version_id == post_processor_version_id,
            MachinePostBinding.control_system_id == eff,
        )
        .limit(1)
    ).scalar_one_or_none()
    if b is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=(
                "Diese Kombination Maschine · Steuerung · Postprozessor ist nicht freigegeben. "
                "Bitte im Admin-Bereich „Fertigungsbindungen“ anlegen oder wählen Sie eine freigegebene Kombination."
            ),
        )


def require_cam_step_model(db: Session, cam_step_model_id: int) -> CamStepModel:
    m = db.get(CamStepModel, cam_step_model_id)
    if m is None or m.deleted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Step-/CAM-Modell ungültig oder archiviert")
    return m


def validate_generated_nc_attachment(db: Session, case_id: int, attachment_id: int | None) -> None:
    if attachment_id is None:
        return
    row = db.get(CaseAttachment, attachment_id)
    if row is None or row.case_id != case_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Der verknüpfte NC-Anhang muss zu diesem Fall gehören.",
        )


def count_cases_for_binding(db: Session, binding: MachinePostBinding) -> int:
    return int(
        db.execute(
            select(func.count())
            .select_from(Case)
            .join(Machine, Case.machine_id == Machine.id)
            .where(
                Case.machine_id == binding.machine_id,
                Case.post_processor_version_id == binding.post_processor_version_id,
                func.coalesce(Case.control_system_id, Machine.control_system_id) == binding.control_system_id,
            )
        ).scalar_one()
    )


def count_cases_for_cam_step_model(db: Session, cam_step_model_id: int) -> int:
    return int(db.execute(select(func.count()).select_from(Case).where(Case.cam_step_model_id == cam_step_model_id)).scalar_one())
