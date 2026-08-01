from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def uid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("project"))
    name: Mapped[str] = mapped_column(String(200))
    business_goal: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("knowledge"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    object_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), default="manual")
    source_id: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("meeting"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    transcript: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("decision"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    meeting_id: Mapped[str | None] = mapped_column(ForeignKey("meetings.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    statement: Mapped[str] = mapped_column(Text)
    evidence_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("task"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    decision_id: Mapped[str | None] = mapped_column(ForeignKey("decisions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    objective: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(40), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
