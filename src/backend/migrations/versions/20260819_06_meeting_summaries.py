"""Persist governed structured meeting summaries.

Revision ID: 20260819_06
Revises: 20260819_05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260819_06"
down_revision = "20260819_05"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "meeting_summaries",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("workspace_id", sa.String(40), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("meeting_id", sa.String(40), sa.ForeignKey("meetings.id"), nullable=False, unique=True),
        sa.Column("snapshot_id", sa.String(40), sa.ForeignKey("meeting_final_snapshots.id"), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meeting_summaries_workspace_id", "meeting_summaries", ["workspace_id"])
    op.create_index("ix_meeting_summaries_meeting_id", "meeting_summaries", ["meeting_id"], unique=True)
    op.create_index("ix_meeting_summaries_snapshot_id", "meeting_summaries", ["snapshot_id"])


def downgrade():
    op.drop_table("meeting_summaries")

