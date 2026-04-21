"""post version code attachment

Revision ID: f8a1_post_version_code
Revises: f2d7_test_case_assets
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8a1_post_version_code"
down_revision: Union[str, None] = "f2d7_test_case_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("post_processor_versions", sa.Column("code_file_name", sa.String(length=512), nullable=True))
    op.add_column("post_processor_versions", sa.Column("code_file_type", sa.String(length=128), nullable=True))
    op.add_column("post_processor_versions", sa.Column("code_storage_path", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("post_processor_versions", "code_storage_path")
    op.drop_column("post_processor_versions", "code_file_type")
    op.drop_column("post_processor_versions", "code_file_name")

