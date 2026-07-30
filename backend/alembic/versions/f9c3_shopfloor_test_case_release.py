"""shopfloor test case release

Revision ID: f9c3_shopfloor_release
Revises: f9b2_agent_runs
Create Date: 2026-05-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9c3_shopfloor_release"
down_revision: Union[str, None] = "f9b2_agent_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_cases",
        sa.Column("shopfloor_released", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("test_cases", "shopfloor_released")
