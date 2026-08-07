from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


ReminderType = Literal["risk", "suggestion", "history", "question", "opportunity"]


class ReminderSource(BaseModel):
    type: str
    id: str
    title: str = ""
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class AIReminder(BaseModel):
    type: ReminderType = "history"
    title: str
    summary: str
    suggestion: str = ""
    reason: str = ""
    sources: list[ReminderSource] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    def websocket_dict(self) -> dict:
        first = self.sources[0] if self.sources else None
        return {
            "type": self.type,
            "title": self.title,
            "summary": self.summary,
            "suggestion": self.suggestion,
            "reason": self.reason,
            "sources": [source.model_dump() for source in self.sources],
            # Sprint 1 frontend compatibility
            "source": {
                "type": first.type if first else "system",
                "id": first.id if first else "ai-reminder",
            },
            "relevanceScore": self.confidence,
            "confidence": self.confidence,
        }


class ReminderEnvelope(BaseModel):
    reminders: list[AIReminder] = Field(default_factory=list)
