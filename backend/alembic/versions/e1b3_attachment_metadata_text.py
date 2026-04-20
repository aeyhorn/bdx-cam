"""attachment metadata and text editing

Revision ID: e1b3_attachment_meta
Revises: d4f2_system_builds
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e1b3_attachment_meta"
down_revision: Union[str, None] = "d4f2_system_builds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("case_attachments", sa.Column("attachment_role", sa.String(length=32), nullable=False, server_default="other"))
    op.add_column("case_attachments", sa.Column("linked_project_name", sa.String(length=255), nullable=True))
    op.add_column("case_attachments", sa.Column("notes", sa.Text(), nullable=True))
    op.alter_column("case_attachments", "attachment_role", server_default=None)


def downgrade() -> None:
    op.drop_column("case_attachments", "notes")
    op.drop_column("case_attachments", "linked_project_name")
    op.drop_column("case_attachments", "attachment_role")
