"""Add governed decision memory with provenance and supersession.

Revision ID: 20260819_07
Revises: 20260819_06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260819_07"
down_revision = "20260819_06"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "decision_memories",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("workspace_id", sa.String(40), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("source_meeting_id", sa.String(40), sa.ForeignKey("meetings.id"), nullable=False),
        sa.Column("source_summary_id", sa.String(40), sa.ForeignKey("meeting_summaries.id"), nullable=False),
        sa.Column("source_decision_id", sa.String(80), nullable=False, unique=True),
        sa.Column("knowledge_item_id", sa.String(40), sa.ForeignKey("knowledge_items.id"), nullable=True, unique=True),
        sa.Column("supersedes_id", sa.String(40), sa.ForeignKey("decision_memories.id"), nullable=True),
        sa.Column("title", sa.String(240), nullable=False), sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(240), nullable=False, server_default=""),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1"),
        sa.Column("source_ids", sa.JSON(), nullable=False), sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("effective_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for name in ("workspace_id", "source_meeting_id", "source_summary_id", "source_decision_id", "status"):
        op.create_index(f"ix_decision_memories_{name}", "decision_memories", [name], unique=name == "source_decision_id")


def downgrade():
    op.drop_table("decision_memories")

