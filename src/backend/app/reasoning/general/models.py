from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.reasoning.models import Finding


GeneralFindingType = Literal[
    "claim",
    "contradiction",
    "missing_information",
    "uncertainty",
    "decision_risk",
]

GeneralCandidateSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class GeneralFindingCandidate(BaseModel):
    """
    Candidate signal proposed by General Reasoner.

    IMPORTANT:
    A candidate is NOT yet a Finding and must never be surfaced as an
    active DecisionOS risk before it passes FindingGate.
    """

    id: str = ""

    type: GeneralFindingType

    domain: str = "general"
    subject: str = ""

    title: str
    summary: str = ""

    severity: GeneralCandidateSeverity = "medium"

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    decisionRelevance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    evidenceSourceIds: list[str] = Field(
        default_factory=list
    )

    # Stable semantic identity used for dedupe/lifecycle identity later.
    # It must describe the issue, not generated wording.
    noveltyKey: str

    # Machine-readable seed for the existing Recommendation layer.
    # Phase 1 stores it on Finding.attributes only; it does not yet modify
    # RecommendationGenerator.
    suggestedAction: str = ""

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )


class GeneralRejectedCandidate(BaseModel):
    candidate: GeneralFindingCandidate
    reason: str
    details: dict[str, Any] = Field(
        default_factory=dict
    )


class GeneralReasoningDiagnostics(BaseModel):
    backend: str = ""

    candidateCount: int = 0
    acceptedCount: int = 0
    rejectedCount: int = 0

    backendErrors: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class GeneralReasoningResult(BaseModel):
    meetingId: str
    contextId: str = ""
    projectId: str = ""

    candidates: list[GeneralFindingCandidate] = Field(
        default_factory=list
    )

    findings: list[Finding] = Field(
        default_factory=list
    )

    rejected: list[GeneralRejectedCandidate] = Field(
        default_factory=list
    )

    diagnostics: GeneralReasoningDiagnostics = Field(
        default_factory=GeneralReasoningDiagnostics
    )
