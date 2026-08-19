from sqlalchemy import select

from app.models.entities import Project


def ensure_default_project(db, workspace_id: str) -> Project:
    """Keep the legacy project boundary internal to the reasoning engine."""
    project = db.scalar(
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .order_by(Project.created_at.asc())
        .limit(1)
    )
    if project:
        return project
    project = Project(workspace_id=workspace_id, name="我的空间", business_goal="")
    db.add(project)
    db.flush()
    return project

