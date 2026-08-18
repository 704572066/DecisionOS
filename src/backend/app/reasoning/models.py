from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.reasoning.context import EvaluationConstraint
#
# Finding describes WHY the current decision situation deserves attention.
#
# It deliberately does not contain business-specific concepts such as:
#
#   discount risk
#   payment risk
#   delivery risk
#
# Those belong to semantic state / knowledge / future evaluator input.
#

FindingType = Literal[
    "risk",
    "conflict",
    "gap",
    "dependency",
    "deviation",
]


FindingStatus = Literal[
    "open",
    "updated",
    "resolved",
    "reopened",
]


FindingSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


FindingSourceType = Literal[
    "semantic_state",
    "decision_state",
    "policy",
    "decision",
    "document",
    "crm",
    "runtime",
    "knowledge",
    "other",
]


class FindingEvidence(BaseModel):
    """
    Evidence supporting a finding.

    The Reasoner should be able to explain where every finding comes from.

    Evidence can refer to:

    - semanticState
    - decisionState
    - company policy
    - previous decisions
    - CRM/history
    - documents
    - runtime observations

    This model intentionally does not depend on retrieval implementation.
    """

    sourceType: FindingSourceType = "other"

    sourceId: str = ""

    title: str = ""

    summary: str = ""

    field: str = ""

    value: Any = None

    actor: str = ""

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class Finding(BaseModel):
    """
    Generic reasoning result produced from current decision context.

    Finding is an internal reasoning object.

    It is NOT a DecisionBoard API model.

    Future flow:

        semanticState
              +
        decisionState
              +
        enterprise knowledge
              +
        historical evidence
              ↓
            Finding
              ↓
        Decision Board adapter
              ↓
        BoardRisk / BoardAction

    No business-specific thresholds or field names belong in this model.
    """

    id: str

    type: FindingType

    status: FindingStatus = "open"

    #
    # Logical location of the issue.
    #
    # Examples:
    #
    # commercial
    # delivery
    # scope
    # approval
    # contract
    #
    # But the model deliberately keeps this open-ended.
    #
    domain: str = ""

    #
    # Stable subject being reasoned about.
    #
    # Examples:
    #
    # discountPercent
    # paymentTermDays
    # legalApproval
    # goLiveDate
    # scopeInclusion
    #
    # The Reasoner does not need dedicated Python models for these.
    #
    subject: str = ""

    title: str

    summary: str = ""

    severity: FindingSeverity = "medium"

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    #
    # Evidence IDs are kept separately for efficient board/API adaptation.
    #
    sourceIds: list[str] = Field(
        default_factory=list
    )

    evidence: list[FindingEvidence] = Field(
        default_factory=list
    )

    #
    # Generic structured explanation of the finding.
    #
    # Future evaluators may put things here such as:
    #
    # {
    #   "expected": ...,
    #   "actual": ...,
    #   "relation": "...",
    #   "difference": ...
    # }
    #
    # No domain-specific schema is forced at this level.
    #
    attributes: dict[str, Any] = Field(
        default_factory=dict
    )

    #
    # Optional machine-readable explanation.
    #
    # This is useful for later lifecycle matching and debugging without
    # forcing the UI to display internal reasoning details.
    #
    reasonCode: str = ""

    #
    # Stable identity key used by the future Finding Store to decide whether
    # a newly evaluated finding represents:
    #
    # OPEN
    # UPDATED
    # RESOLVED
    # REOPENED
    #
    # Example shape:
    #
    # conflict:commercial:discountPercent
    #
    # The model itself does not decide how the key is generated.
    #
    fingerprint: str = ""

    firstObservedAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    resolvedAt: datetime | None = None


class FindingSet(BaseModel):
    """
    Result container for one Reasoner evaluation cycle.

    Keeping this object now prevents future Reasoner APIs from returning
    unstructured list/dict combinations.
    """

    meetingId: str

    contextId: str = ""

    findings: list[Finding] = Field(
        default_factory=list
    )

    evaluatedAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    diagnostics: dict[str, Any] = Field(
        default_factory=dict
    )


from app.reasoning.recommendation_models import Recommendation
from app.intervention.models import InterventionDecision


class ReasoningDiagnostics(BaseModel):
    evaluationContextBuilt: bool = False

    knowledgeCount: int = 0

    compiledConstraintCount: int = 0
    rejectedConstraintCount: int = 0

    triggeredFindingCount: int = 0
    activeFindingCount: int = 0
    resolvedFindingCount: int = 0

    enterpriseFindingCount: int = 0
    generalFindingCount: int = 0
    mergedFindingCount: int = 0
    suppressedGeneralFindingCount: int = 0
    normativeSuppressedGeneralFindingCount: int = 0

    generatedRecommendationCount: int = 0
    activeRecommendationCount: int = 0
    obsoleteRecommendationCount: int = 0

    interventionCount: int = 0
    interruptInterventionCount: int = 0
    surfaceInterventionCount: int = 0
    silentInterventionCount: int = 0

    compilationErrors: list[str] = Field(default_factory=list)
    evaluationErrors: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)


class ReasoningResult(BaseModel):
    meetingId: str
    contextId: str = ""
    projectId: str = ""

    findings: list[Finding] = Field(default_factory=list)
    constraints: list[EvaluationConstraint] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    interventions: list[InterventionDecision] = Field(default_factory=list)

    diagnostics: ReasoningDiagnostics = Field(
        default_factory=ReasoningDiagnostics
    )