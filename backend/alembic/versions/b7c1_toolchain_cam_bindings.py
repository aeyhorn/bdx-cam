"""toolchain: cam step models, machine-post bindings, case links

Revision ID: b7c1_toolchain
Revises: aa2acfe687a9
Create Date: 2026-04-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "b7c1_toolchain"
down_revision: Union[str, None] = "aa2acfe687a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cam_step_models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("revision", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cam_step_models_code"), "cam_step_models", ["code"], unique=True)

    op.create_table(
        "machine_post_bindings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_id", sa.Integer(), nullable=False),
        sa.Column("post_processor_version_id", sa.Integer(), nullable=False),
        sa.Column("control_system_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["control_system_id"], ["control_systems.id"]),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"]),
        sa.ForeignKeyConstraint(["post_processor_version_id"], ["post_processor_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("machine_id", "post_processor_version_id", "control_system_id", name="uq_machine_post_control"),
    )

    op.add_column("cases", sa.Column("cam_step_model_id", sa.Integer(), nullable=True))
    op.add_column("cases", sa.Column("generated_nc_attachment_id", sa.Integer(), nullable=True))

    conn = op.get_bind()

    conn.execute(
        text(
            """
            INSERT INTO cam_step_models (code, name, revision, notes, created_at, updated_at)
            SELECT 'LEGACY', 'Import / Altbestand', NULL, 'Automatisch für bestehende Fälle', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            WHERE NOT EXISTS (SELECT 1 FROM cam_step_models WHERE code = 'LEGACY')
            """
        )
    )

    legacy_id = conn.execute(text("SELECT id FROM cam_step_models WHERE code = 'LEGACY' LIMIT 1")).scalar()
    assert legacy_id is not None
    conn.execute(text("UPDATE cases SET cam_step_model_id = :lid WHERE cam_step_model_id IS NULL"), {"lid": legacy_id})

    cs_fb = conn.execute(
        text("SELECT id FROM control_systems WHERE deleted_at IS NULL ORDER BY id LIMIT 1")
    ).scalar()
    if cs_fb is not None:
        conn.execute(
            text(
                """
                UPDATE cases AS c
                SET control_system_id = :cs
                FROM machines AS m
                WHERE c.machine_id = m.id
                  AND c.control_system_id IS NULL
                  AND m.control_system_id IS NULL
                """
            ),
            {"cs": cs_fb},
        )
        conn.execute(
            text(
                """
                UPDATE machines AS m
                SET control_system_id = :cs
                WHERE m.control_system_id IS NULL
                  AND m.deleted_at IS NULL
                """
            ),
            {"cs": cs_fb},
        )

    conn.execute(
        text(
            """
            INSERT INTO machine_post_bindings (machine_id, post_processor_version_id, control_system_id, notes, created_at, updated_at)
            SELECT DISTINCT c.machine_id, c.post_processor_version_id, COALESCE(c.control_system_id, m.control_system_id), 'Migriert aus Fällen', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM cases c
            JOIN machines m ON m.id = c.machine_id
            WHERE COALESCE(c.control_system_id, m.control_system_id) IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM machine_post_bindings b
                WHERE b.machine_id = c.machine_id
                  AND b.post_processor_version_id = c.post_processor_version_id
                  AND b.control_system_id = COALESCE(c.control_system_id, m.control_system_id)
              )
            """
        )
    )

    op.create_foreign_key("fk_cases_cam_step_model", "cases", "cam_step_models", ["cam_step_model_id"], ["id"])
    op.create_foreign_key(
        "fk_cases_generated_nc_attachment",
        "cases",
        "case_attachments",
        ["generated_nc_attachment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("cases", "cam_step_model_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_cases_generated_nc_attachment", "cases", type_="foreignkey")
    op.drop_constraint("fk_cases_cam_step_model", "cases", type_="foreignkey")
    op.drop_column("cases", "generated_nc_attachment_id")
    op.drop_column("cases", "cam_step_model_id")
    op.drop_table("machine_post_bindings")
    op.drop_index(op.f("ix_cam_step_models_code"), table_name="cam_step_models")
    op.drop_table("cam_step_models")
