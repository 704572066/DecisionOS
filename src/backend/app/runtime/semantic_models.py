from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SemanticDomain = Literal[
    "commercial",
    "delivery",
    "scope",
    "resource",
    "contract",
    "commitment",
    "approval",
    "decision",
    "unknown",
    "other",
]

SemanticKind = Literal[
    "fact_change",
    "constraint",
    "commitment",
    "dependency",
    "scope_change",
    "resource_constraint",
    "liability",
    "decision",
    "unknown",
]


class SemanticEventCandidate(BaseModel):
    domain: SemanticDomain
    kind: SemanticKind
    field: str = ""
    value: Any = None
    normalizedValue: Any = None
    relation: str = ""
    actor: str = "unknown"
    target: str = ""
    status: str = ""
    sourceText: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class SemanticEventEnvelope(BaseModel):
    events: list[SemanticEventCandidate] = Field(default_factory=list)
