from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ConstraintOperator = Literal[
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",

    "in",
    "not_in",

    "exists",
    "missing",

    "requires",
    "depends_on",

    "conflicts_with",
]


ConstraintEffect = Literal[
    "risk",
    "conflict",
    "gap",
    "dependency",
    "deviation",
]


ConstraintSubjectSource = Literal[
    "semantic_state",
    "decision_state",
    "either",
]


class EvaluationSubject(BaseModel):
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


class ConstraintOperand(BaseModel):
    """
    Machine-readable reference to another subject.

    Used for relational constraints such as:

        discountPercent > 10
            requires
        paymentTermEvaluation exists

    or:

        goLiveDate
            conflicts_with
        resourceCapacity

    This object references structure, not business meaning.
    """

    domain: str = ""

    subject: str

    operator: ConstraintOperator = "exists"

    expectedValue: Any = None

    source: ConstraintSubjectSource = "either"

    actor: str = ""

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )


class EvaluationConstraint(BaseModel):
    """
    Machine-executable enterprise constraint.

    This model is the boundary between:

        natural-language enterprise knowledge
                    ↓
            Constraint Compiler
                    ↓
        EvaluationConstraint
                    ↓
             Generic Evaluator

    The evaluator must never need to understand the natural-language
    policy that produced this object.
    """

    id: str

    #
    # Where this constraint conceptually belongs.
    #
    domain: str = ""

    #
    # Primary subject being evaluated.
    #
    subject: str

    #
    # Which state surface should supply the actual value.
    #
    subjectSource: ConstraintSubjectSource = "either"

    #
    # Optional participant ownership filter.
    #
    # Example:
    # customer / us / third_party
    #
    actor: str = ""

    #
    # Primary comparison / relation.
    #
    operator: ConstraintOperator

    expectedValue: Any = None

    #
    # Optional second operand.
    #
    # Used for:
    #
    # requires
    # depends_on
    # conflicts_with
    #
    operand: ConstraintOperand | None = None

    #
    # What kind of Finding should be produced when the constraint
    # condition is satisfied / violated according to evaluationMode.
    #
    findingType: ConstraintEffect = "risk"

    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = "medium"

    #
    # Determines when a Finding should be emitted.
    #
    # "on_match":
    #     emit when actual matches the condition
    #
    # "on_mismatch":
    #     emit when actual violates the condition
    #
    evaluationMode: Literal[
        "on_match",
        "on_mismatch",
    ] = "on_mismatch"

    title: str = ""

    description: str = ""

    #
    # Original enterprise evidence.
    #
    sourceIds: list[str] = Field(
        default_factory=list
    )

    #
    # Generic metadata for compiler/evaluator extensions.
    #
    attributes: dict[str, Any] = Field(
        default_factory=dict
    )


class EvaluationContext(BaseModel):
    meetingId: str

    contextId: str = ""

    projectId: str = ""

    objective: str = ""

    semanticSubjects: list[EvaluationSubject] = Field(
        default_factory=list
    )

    decisionSubjects: list[EvaluationSubject] = Field(
        default_factory=list
    )

    knowledge: list[EvaluationKnowledge] = Field(
        default_factory=list
    )

    constraints: list[EvaluationConstraint] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )