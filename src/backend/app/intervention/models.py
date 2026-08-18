from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


InterventionLevel = Literal[
    "silent",
    "surface",
    "interrupt",
]

InterventionUrgency = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class InterventionDecision(BaseModel):
    """Deterministic decision about whether a Finding deserves interruption."""

    id: str
    workspaceId: str = ""
    meetingId: str = ""
    contextId: str = ""

    findingId: str = ""
    recommendationId: str = ""

    level: InterventionLevel = "silent"
    reasonCode: str = ""

    title: str = ""
    message: str = ""

    score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: str = "medium"
    urgency: InterventionUrgency = "low"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    decisionRelevance: float = Field(default=0.5, ge=0.0, le=1.0)
    actionability: float = Field(default=0.0, ge=0.0, le=1.0)

    sourceIds: list[str] = Field(default_factory=list)
    fingerprint: str = ""

    evaluatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    diagnostics: dict[str, Any] = Field(default_factory=dict)


class InterventionSet(BaseModel):
    meetingId: str
    contextId: str = ""
    decisions: list[InterventionDecision] = Field(default_factory=list)
    highestLevel: InterventionLevel = "silent"
    evaluatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    diagnostics: dict[str, Any] = Field(default_factory=dict)
