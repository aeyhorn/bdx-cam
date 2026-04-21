"""agent runs

Revision ID: f9b2_agent_runs
Revises: f8a1_post_version_code
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9b2_agent_runs"
down_revision: Union[str, None] = "f8a1_post_version_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("test_case_id", sa.Integer(), nullable=True),
        sa.Column("trigger_mode", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("agent_type", sa.String(length=64), nullable=False, server_default="error_analysis"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("input_snapshot", sa.JSON(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("output_structured", sa.JSON(), nullable=True),
        sa.Column("knowledge_entry_id", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_by", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_entry_id"], ["knowledge_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["started_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_case_id", "agent_runs", ["case_id"], unique=False)
    op.create_index("ix_agent_runs_test_case_id", "agent_runs", ["test_case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_runs_test_case_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_case_id", table_name="agent_runs")
    op.drop_table("agent_runs")

