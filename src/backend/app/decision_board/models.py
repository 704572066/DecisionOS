from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from app.reasoning.models import Finding
from app.reasoning.context import EvaluationConstraint
from app.reasoning.recommendation_models import Recommendation
DecisionStatus = Literal[
    "gathering_information",
    "negotiating",
    "waiting_confirmation",
    "ready_to_decide",
]

class DecisionBoardReasoning(BaseModel):

    findings: list[Finding] = Field(
        default_factory=list
    )

    constraints: list[EvaluationConstraint] = Field(
        default_factory=list
    )

    recommendations: list[Recommendation] = Field(
        default_factory=list
    )

    diagnostics: dict = Field(
        default_factory=dict
    )

class BoardRisk(BaseModel):
    title: str
    summary: str
    severity: Literal["low", "medium", "high"] = "medium"
    sourceIds: list[str] = Field(default_factory=list)


class BoardEvidence(BaseModel):
    id: str
    type: str
    title: str
    summary: str = ""
    score: float = Field(default=0, ge=0, le=1)


class BoardAction(BaseModel):
    text: str
    sourceIds: list[str] = Field(default_factory=list)


class DecisionBoard(BaseModel):
    meetingId: str
    projectId: str
    contextId: str
    reasoning: DecisionBoardReasoning = Field(
        default_factory=DecisionBoardReasoning
    )
    objective: str = ""
    status: DecisionStatus = "gathering_information"

    # This means information readiness, not probability that a decision is right.
    decisionReadiness: int = Field(default=0, ge=0, le=100)

    risks: list[BoardRisk] = Field(default_factory=list)
    evidence: list[BoardEvidence] = Field(default_factory=list)
    actions: list[BoardAction] = Field(default_factory=list)
    currentConditions: dict = Field(default_factory=dict)
    recentEvents: list[dict] = Field(default_factory=list)
    resolvedRisks: list[str] = Field(default_factory=list)
    updatedAt: datetime
    diagnostics: dict = Field(default_factory=dict)
