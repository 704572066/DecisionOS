from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


SourceKind = Literal["transcript", "event", "semantic", "finding", "knowledge"]


class SummaryItemCandidate(BaseModel):
    text: str
    sourceIds: list[str] = Field(default_factory=list)


class SummaryCandidate(BaseModel):
    summary: str = ""
    keyFacts: list[SummaryItemCandidate] = Field(default_factory=list)
    decisions: list[SummaryItemCandidate] = Field(default_factory=list)
    actionItems: list[SummaryItemCandidate] = Field(default_factory=list)
    openIssues: list[SummaryItemCandidate] = Field(default_factory=list)


class SummaryEvidence(BaseModel):
    sourceId: str
    sourceType: SourceKind
    text: str
    metadata: dict = Field(default_factory=dict)


class MeetingSummaryResult(BaseModel):
    meetingId: str
    summary: str = ""
    keyFacts: list[SummaryItemCandidate] = Field(default_factory=list)
    decisions: list[SummaryItemCandidate] = Field(default_factory=list)
    actionItems: list[SummaryItemCandidate] = Field(default_factory=list)
    openIssues: list[SummaryItemCandidate] = Field(default_factory=list)
    evidence: list[SummaryEvidence] = Field(default_factory=list)
    generatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    diagnostics: dict = Field(default_factory=dict)

