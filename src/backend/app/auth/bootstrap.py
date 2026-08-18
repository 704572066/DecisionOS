from sqlalchemy import select
from app.auth.passwords import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import User, Workspace

def bootstrap_legacy_owner() -> None:
    if not settings.bootstrap_user_email or not settings.bootstrap_user_password:
        return
    db=SessionLocal()
    try:
        email=settings.bootstrap_user_email.lower().strip()
        if db.scalar(select(User).where(User.email==email)): return
        workspace=db.get(Workspace,"workspace-legacy")
        if not workspace: return
        user=User(email=email,username="Legacy User",password_hash=hash_password(settings.bootstrap_user_password),workspace_id=workspace.id)
        db.add(user); db.flush(); workspace.owner_user_id=user.id; db.commit()
    finally: db.close()
