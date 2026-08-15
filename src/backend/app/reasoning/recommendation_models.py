from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.reasoning.models import (
    FindingEvidence,
)


RecommendationType = Literal[
    "action",
    "clarification",
    "negotiation",
    "assessment",
    "approval",
    "monitoring",
]


RecommendationStatus = Literal[
    "open",
    "accepted",
    "dismissed",
    "completed",
    "obsolete",
]


RecommendationPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class Recommendation(BaseModel):
    """
    Generic action recommendation produced from reasoning findings.

    Finding answers:

        "What deserves attention?"

    Recommendation answers:

        "What should the user do next?"

    Recommendation deliberately remains separate from Finding.

    Example:

        Finding:
            discountPercent > 10 requires
            paymentTermAssessment

        Recommendation:
            Complete payment-term assessment before
            confirming the discount condition.

    This model contains no business-specific field definitions
    or thresholds.
    """

    id: str

    meetingId: str = ""

    #
    # Finding that caused this recommendation.
    #
    findingId: str = ""

    type: RecommendationType = "action"

    status: RecommendationStatus = "open"

    #
    # Logical reasoning location.
    #
    domain: str = ""

    subject: str = ""

    title: str

    summary: str = ""

    #
    # Short executable action statement.
    #
    # Example:
    #
    # "在确认折扣前完成付款周期评估。"
    #
    action: str = ""

    priority: RecommendationPriority = "medium"

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    #
    # Provenance used to explain the recommendation.
    #
    sourceIds: list[str] = Field(
        default_factory=list
    )

    evidence: list[FindingEvidence] = Field(
        default_factory=list
    )

    #
    # Machine-readable metadata.
    #
    # Future generators may place structured information here:
    #
    # {
    #   "findingType": "dependency",
    #   "constraintId": "...",
    #   "recommendedSubject": "...",
    #   "recommendedOperator": "exists"
    # }
    #
    attributes: dict[str, Any] = Field(
        default_factory=dict
    )

    #
    # Stable machine-readable explanation.
    #
    reasonCode: str = ""

    #
    # Stable identity for lifecycle matching.
    #
    # Recommendation lifecycle should not depend on generated title/action
    # text because those may evolve over time.
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

    completedAt: datetime | None = None

    dismissedAt: datetime | None = None


class RecommendationSet(BaseModel):
    """
    Recommendations produced during one reasoning cycle.

    This mirrors FindingSet so future runtime integration does not
    return unstructured lists.
    """

    meetingId: str

    contextId: str = ""

    recommendations: list[Recommendation] = Field(
        default_factory=list
    )

    generatedAt: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    diagnostics: dict[str, Any] = Field(
        default_factory=dict
    )