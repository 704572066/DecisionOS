"""Meeting lifecycle and immutable final snapshots.

Revision ID: 20260819_04
Revises: 20260819_03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260819_04"
down_revision = "20260819_03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("meetings", sa.Column("ended_at", sa.DateTime(), nullable=True))
    op.add_column("meetings", sa.Column("finalized_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE meetings SET status='active' WHERE status='in_progress'")
    op.create_index("ix_meetings_status", "meetings", ["status"])
    op.create_table(
        "meeting_final_snapshots",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("workspace_id", sa.String(40), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("meeting_id", sa.String(40), sa.ForeignKey("meetings.id"), nullable=False, unique=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meeting_final_snapshots_workspace_id", "meeting_final_snapshots", ["workspace_id"])
    op.create_index("ix_meeting_final_snapshots_meeting_id", "meeting_final_snapshots", ["meeting_id"], unique=True)
    op.create_table(
        "meeting_dialogue_turns",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("workspace_id", sa.String(40), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("meeting_id", sa.String(40), sa.ForeignKey("meetings.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meeting_dialogue_turns_workspace_id", "meeting_dialogue_turns", ["workspace_id"])
    op.create_index("ix_meeting_dialogue_turns_meeting_id", "meeting_dialogue_turns", ["meeting_id"])


def downgrade():
    op.drop_table("meeting_dialogue_turns")
    op.drop_table("meeting_final_snapshots")
    op.drop_index("ix_meetings_status", table_name="meetings")
    op.drop_column("meetings", "finalized_at")
    op.drop_column("meetings", "ended_at")

