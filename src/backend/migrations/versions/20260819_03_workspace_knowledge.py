"""Promote all knowledge to the workspace scope.

Revision ID: 20260819_03
Revises: 20260818_02
"""
from alembic import op

revision = "20260819_03"
down_revision = "20260818_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE knowledge_items SET project_id = NULL WHERE project_id IS NOT NULL")
    op.execute("UPDATE knowledge_sources SET project_id = NULL WHERE project_id IS NOT NULL")


def downgrade():
    # Workspace-scoped knowledge cannot be safely assigned back to a project.
    pass

