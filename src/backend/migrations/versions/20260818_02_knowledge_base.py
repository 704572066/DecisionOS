"""Phase 3.2 knowledge base management.

Revision ID: 20260818_02
Revises: 20260818_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260818_02"
down_revision = "20260818_01"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("knowledge_items", "project_id", existing_type=sa.String(40), nullable=True)
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("workspace_id", sa.String(40), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(40), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("object_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("media_type", sa.String(160), nullable=False, server_default="application/octet-stream"),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="uploaded"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_sources_workspace_id", "knowledge_sources", ["workspace_id"])
    op.create_index("ix_knowledge_sources_project_id", "knowledge_sources", ["project_id"])
    op.create_index("ix_knowledge_sources_status", "knowledge_sources", ["status"])
    op.create_index("ix_knowledge_sources_object_type", "knowledge_sources", ["object_type"])


def downgrade():
    op.drop_table("knowledge_sources")
    op.alter_column("knowledge_items", "project_id", existing_type=sa.String(40), nullable=False)

