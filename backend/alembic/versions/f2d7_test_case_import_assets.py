"""test case import assets

Revision ID: f2d7_test_case_assets
Revises: e1b3_attachment_meta
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2d7_test_case_assets"
down_revision: Union[str, None] = "e1b3_attachment_meta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_case_attachments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("file_type", sa.String(length=128), nullable=True),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("attachment_role", sa.String(length=32), nullable=False, server_default="program"),
        sa.Column("linked_project_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_case_attachments_test_case_id", "test_case_attachments", ["test_case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_test_case_attachments_test_case_id", table_name="test_case_attachments")
    op.drop_table("test_case_attachments")
