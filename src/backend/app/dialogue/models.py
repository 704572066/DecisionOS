from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


DialogueIntent = Literal[
    "meeting_context",
    "explanation",
    "recommendation",
    "analysis",
    "general",
]


class DialogueTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class DialogueRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=4000,
    )


class DialogueResponse(BaseModel):
    meetingId: str
    conversationId: str

    answer: str

    intent: DialogueIntent = "general"

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    sourceIds: list[str] = Field(
        default_factory=list
    )

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    diagnostics: dict = Field(
        default_factory=dict
    )
