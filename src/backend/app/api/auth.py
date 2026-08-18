from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import create_session, revoke_session
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User, Workspace

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterBody(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=200)
    username: str = Field(default="", max_length=120)

class LoginBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str

def public_identity(identity: CurrentIdentity):
    return {"user": {"id": identity.user.id, "email": identity.user.email, "username": identity.user.username, "status": identity.user.status}, "workspace": {"id": identity.workspace.id, "name": identity.workspace.name}}

def set_cookie(response: Response, token: str):
    response.set_cookie(settings.auth_cookie_name, token, max_age=settings.auth_session_days * 86400, httponly=True, secure=settings.auth_cookie_secure, samesite="lax", path="/")

@router.post("/register", status_code=201)
def register(body: RegisterBody, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    try:
        user = User(email=email, username=body.username.strip(), password_hash=hash_password(body.password))
        db.add(user); db.flush()
        workspace = Workspace(name=(body.username.strip() or email.split("@")[0]) + " 的空间", owner_user_id=user.id)
        db.add(workspace); db.flush()
        user.workspace_id = workspace.id
        db.commit(); db.refresh(user); db.refresh(workspace)
    except Exception:
        db.rollback(); raise
    set_cookie(response, create_session(db, user))
    return public_identity(CurrentIdentity(user, workspace))

@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower().strip()))
    if not user or user.status != "active" or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    workspace = db.get(Workspace, user.workspace_id)
    if not workspace:
        raise HTTPException(401, "Workspace unavailable")
    set_cookie(response, create_session(db, user))
    return public_identity(CurrentIdentity(user, workspace))

@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    revoke_session(db, request.cookies.get(settings.auth_cookie_name))
    response.delete_cookie(settings.auth_cookie_name, path="/")

@router.get("/me")
def me(identity: CurrentIdentity = Depends(get_current_identity)):
    return public_identity(identity)
