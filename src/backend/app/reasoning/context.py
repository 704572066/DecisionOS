from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationSubject(BaseModel):
    """
    A normalized subject currently visible to the Reasoner.

    It may come from semanticState or decisionState.

    Examples:
    - discountPercent
    - paymentTermDays
    - goLiveDate
    - legalApproval
    - scopeInclusion

    The model is intentionally domain-neutral.
    """

    domain: str = ""

    field: str

    value: Any = None

    actor: str = ""

    role: str = ""

    status: str = ""

    relation: str = ""

    sourceText: str = ""

    sourceType: str = ""

    sourceId: str = ""

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class EvaluationKnowledge(BaseModel):
    """
    Knowledge/evidence available to the evaluator.

    This is deliberately generic and does not assume that the object
    is already a machine-executable policy.

    sourceType may be:
    - policy
    - decision
    - crm
    - document
    - knowledge
    - other
    """

    id: str

    sourceType: str = "knowledge"

    title: str = ""

    summary: str = ""

    content: str = ""

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )


class EvaluationConstraint(BaseModel):
    """
    Machine-evaluable constraint.

    The Generic Evaluator only understands this structure.

    It does NOT know what discount, payment term, delivery date,
    or legal approval mean as business concepts.

    Examples:

    subject = "discountPercent"
    operator = ">"
    expectedValue = 10

    subject = "legalApproval"
    operator = "requires"
    expectedValue = True
    """

    id: str

    domain: str = ""

    subject: str

    operator: str

    expectedValue: Any = None

    severity: str = "medium"

    findingType: str = "risk"

    title: str = ""

    description: str = ""

    sourceIds: list[str] = Field(
        default_factory=list
    )

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )


class EvaluationContext(BaseModel):
    """
    Complete input for one reasoning cycle.

    Future flow:

        RuntimeState
            ↓
        EvaluationContextBuilder
            ↓
        Generic Evaluator
            ↓
        FindingSet
    """

    meetingId: str

    contextId: str = ""

    projectId: str = ""

    objective: str = ""

    #
    # Current participant positions.
    #
    semanticSubjects: list[EvaluationSubject] = Field(
        default_factory=list
    )

    #
    # Current effective decision surface.
    #
    decisionSubjects: list[EvaluationSubject] = Field(
        default_factory=list
    )

    #
    # Retrieved enterprise/history evidence.
    #
    knowledge: list[EvaluationKnowledge] = Field(
        default_factory=list
    )

    #
    # Only already-structured constraints belong here.
    #
    # 3-4.2-A does not attempt to convert natural-language policy
    # documents into constraints yet.
    #
    constraints: list[EvaluationConstraint] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )