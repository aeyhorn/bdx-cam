"""system build versions

Revision ID: d4f2_system_builds
Revises: b7c1_toolchain
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4f2_system_builds"
down_revision: Union[str, None] = "b7c1_toolchain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_build_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component", sa.String(length=128), nullable=False),
        sa.Column("version_label", sa.String(length=128), nullable=False),
        sa.Column("build_no", sa.Integer(), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("is_deployed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_system_build_versions_component"), "system_build_versions", ["component"], unique=False)
    op.create_index(op.f("ix_system_build_versions_created_at"), "system_build_versions", ["created_at"], unique=False)
    op.create_index(
        "ix_system_build_versions_component_build_no",
        "system_build_versions",
        ["component", "build_no"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_system_build_versions_component_build_no", table_name="system_build_versions")
    op.drop_index(op.f("ix_system_build_versions_created_at"), table_name="system_build_versions")
    op.drop_index(op.f("ix_system_build_versions_component"), table_name="system_build_versions")
    op.drop_table("system_build_versions")
