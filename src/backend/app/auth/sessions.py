from datetime import datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import select

from app.core.config import settings
from app.models.entities import AuthSession, User

def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()

def create_session(db, user: User) -> str:
    token = token_urlsafe(48)
    db.add(AuthSession(user_id=user.id, token_hash=token_digest(token), expires_at=datetime.utcnow() + timedelta(days=settings.auth_session_days)))
    db.commit()
    return token

def resolve_session(db, token: str | None) -> User | None:
    if not token:
        return None
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token), AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.utcnow()))
    if not session:
        return None
    user = db.get(User, session.user_id)
    return user if user and user.status == "active" and user.workspace_id else None

def revoke_session(db, token: str | None) -> None:
    if not token:
        return
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token), AuthSession.revoked_at.is_(None)))
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()
