from fastapi import HTTPException
from sqlalchemy import select

from app.models.entities import Meeting, Project

def owned_project(db, workspace_id: str, project_id: str) -> Project:
    value = db.scalar(select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id))
    if not value:
        raise HTTPException(404, "Project not found")
    return value

def owned_meeting(db, workspace_id: str, meeting_id: str) -> Meeting:
    value = db.scalar(select(Meeting).where(Meeting.id == meeting_id, Meeting.workspace_id == workspace_id))
    if not value:
        raise HTTPException(404, "Meeting not found")
    return value
