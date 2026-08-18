from dataclasses import dataclass

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User, Workspace
from app.auth.sessions import resolve_session

@dataclass(frozen=True)
class CurrentIdentity:
    user: User
    workspace: Workspace

def get_current_identity(request: Request, db: Session = Depends(get_db)) -> CurrentIdentity:
    user = resolve_session(db, request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Authentication required")
    workspace = db.get(Workspace, user.workspace_id)
    if not workspace:
        raise HTTPException(401, "Workspace unavailable")
    return CurrentIdentity(user=user, workspace=workspace)
