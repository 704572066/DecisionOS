from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class RuntimeState(BaseModel):
    meetingId: str
    projectId: str
    contextId: str
    objective: str = ""
    canonicalContext: str = ""
    topics: list[str] = Field(default_factory=list)
    facts: list[dict] = Field(default_factory=list)
    constraints: list[dict] = Field(default_factory=list)
    retrievalMode: str = "keyword"
    retrievalResults: list[dict] = Field(default_factory=list)
    rerankedEvidence: list[dict] = Field(default_factory=list)
    reminders: list[dict] = Field(default_factory=list)

    # Sprint 3-2.2 runtime-only decision state.
    decisionFacts: dict = Field(default_factory=dict)
    # Sprint 3-3.3.2: current effective decision conditions resolved from semanticState.
    decisionState: dict = Field(default_factory=dict)
    recentEvents: list[dict] = Field(default_factory=list)
    resolvedRiskKeys: list[str] = Field(default_factory=list)

    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    diagnostics: dict = Field(default_factory=dict)
    lastProcessedSegmentSequence: int = 0
