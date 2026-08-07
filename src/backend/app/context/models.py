from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ContextEntity(BaseModel):
    name: str
    entityType: str = "unknown"
    confidence: float = Field(default=0.7, ge=0, le=1)
    mentions: int = Field(default=1, ge=1)


class ContextFact(BaseModel):
    text: str
    factType: Literal[
        "amount", "percentage", "duration", "date", "constraint", "statement"
    ] = "statement"
    normalizedValue: str | None = None
    sourceText: str = ""


class ContextReference(BaseModel):
    objectType: str
    objectId: str
    title: str
    summary: str = ""
    sourceType: str = ""
    relevanceScore: float = Field(default=0.0, ge=0, le=1)


class ContextConstraint(BaseModel):
    constraintType: str
    description: str
    source: str = "meeting"
    severity: Literal["info", "warning", "critical"] = "info"


class TranscriptCleaningMetadata(BaseModel):
    rawSegments: int = 0
    cleanSegments: int = 0
    removedSegments: int = 0
    mergedSegments: int = 0
    replacements: int = 0
    consolidatedSentences: int = 0
    incompleteSegments: int = 0


class ContextMetadata(BaseModel):
    builderVersion: str = "context-builder-v0.1.2"
    generatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    transcriptCharacters: int = 0
    analyzedCharacters: int = 0
    cleanTranscriptCharacters: int = 0
    cleaning: TranscriptCleaningMetadata = Field(
        default_factory=TranscriptCleaningMetadata
    )


class BusinessContext(BaseModel):
    contextId: str
    projectId: str
    meetingId: str | None = None
    intent: str = ""
    currentObjective: str = ""
    transcriptWindow: str = ""
    cleanTranscriptWindow: str = ""
    topics: list[str] = Field(default_factory=list)
    entities: list[ContextEntity] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    facts: list[ContextFact] = Field(default_factory=list)
    constraints: list[ContextConstraint] = Field(default_factory=list)
    references: list[ContextReference] = Field(default_factory=list)
    metadata: ContextMetadata = Field(default_factory=ContextMetadata)
