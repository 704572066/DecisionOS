"""Personal Workspace and Authentication boundary."""
from alembic import op
import sqlalchemy as sa

revision="20260818_01"
down_revision=None
branch_labels=None
depends_on=None
BUSINESS_TABLES=("projects","knowledge_items","meetings","meeting_transcript_segments","decisions","tasks")

def upgrade():
    op.create_table("workspaces",sa.Column("id",sa.String(40),primary_key=True),sa.Column("name",sa.String(200),nullable=False),sa.Column("owner_user_id",sa.String(40),nullable=True),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.func.now()))
    op.create_table("users",sa.Column("id",sa.String(40),primary_key=True),sa.Column("email",sa.String(320),nullable=False),sa.Column("username",sa.String(120),nullable=False,server_default=""),sa.Column("password_hash",sa.String(500),nullable=False),sa.Column("status",sa.String(40),nullable=False,server_default="active"),sa.Column("workspace_id",sa.String(40),sa.ForeignKey("workspaces.id"),nullable=True),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("email"),sa.UniqueConstraint("workspace_id"))
    op.create_foreign_key("fk_workspaces_owner_user","workspaces","users",["owner_user_id"],["id"])
    op.create_unique_constraint("uq_workspaces_owner_user","workspaces",["owner_user_id"])
    op.create_table("auth_sessions",sa.Column("id",sa.String(40),primary_key=True),sa.Column("user_id",sa.String(40),sa.ForeignKey("users.id"),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False),sa.Column("expires_at",sa.DateTime(),nullable=False),sa.Column("revoked_at",sa.DateTime(),nullable=True),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("token_hash"))
    op.execute("INSERT INTO workspaces (id,name,created_at,updated_at) VALUES ('workspace-legacy','Legacy Personal Workspace',NOW(),NOW())")
    for table in BUSINESS_TABLES:
        op.add_column(table,sa.Column("workspace_id",sa.String(40),nullable=True))
        op.execute(f"UPDATE {table} SET workspace_id='workspace-legacy' WHERE workspace_id IS NULL")
        op.alter_column(table,"workspace_id",nullable=False)
        op.create_foreign_key(f"fk_{table}_workspace",table,"workspaces",["workspace_id"],["id"])
        op.create_index(f"ix_{table}_workspace_id",table,["workspace_id"])
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_index("ix_auth_sessions_token_hash","auth_sessions",["token_hash"],unique=True)

def downgrade():
    for table in reversed(BUSINESS_TABLES):
        op.drop_index(f"ix_{table}_workspace_id",table_name=table)
        op.drop_constraint(f"fk_{table}_workspace",table,type_="foreignkey")
        op.drop_column(table,"workspace_id")
    op.drop_table("auth_sessions"); op.drop_constraint("fk_workspaces_owner_user","workspaces",type_="foreignkey"); op.drop_table("users"); op.drop_table("workspaces")
