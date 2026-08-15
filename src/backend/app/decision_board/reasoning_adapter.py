from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.decision_board.models import BoardAction, BoardRisk
from app.reasoning.models import Finding
from app.reasoning.recommendation_models import Recommendation


@dataclass
class DecisionBoardProjection:
    risks: list[BoardRisk]
    actions: list[BoardAction]
    diagnostics: dict[str, Any]


class ReasoningDecisionBoardAdapter:
    ACTIVE_FINDING_STATUSES = {"open", "updated", "reopened"}
    ACTIVE_RECOMMENDATION_STATUSES = {"open", "accepted"}

    def project(self, *, findings, recommendations) -> DecisionBoardProjection:
        risks = []
        actions = []
        skipped_findings = []
        skipped_recommendations = []

        for finding in findings:
            if finding.status not in self.ACTIVE_FINDING_STATUSES:
                skipped_findings.append({
                    "findingId": finding.id,
                    "status": finding.status,
                    "reason": "inactive_finding",
                })
                continue
            severity = "high" if finding.severity == "critical" else finding.severity
            risks.append(BoardRisk(
                title=finding.title,
                summary=finding.summary,
                severity=severity,
                sourceIds=list(dict.fromkeys(finding.sourceIds))[:3],
            ))

        for recommendation in recommendations:
            if recommendation.status not in self.ACTIVE_RECOMMENDATION_STATUSES:
                skipped_recommendations.append({
                    "recommendationId": recommendation.id,
                    "status": recommendation.status,
                    "reason": "inactive_recommendation",
                })
                continue
            text = recommendation.action.strip() or recommendation.title.strip()
            if not text:
                continue
            actions.append(BoardAction(
                text=text,
                sourceIds=list(dict.fromkeys(recommendation.sourceIds))[:3],
            ))

        return DecisionBoardProjection(
            risks=risks,
            actions=actions,
            diagnostics={
                "findingCount": len(findings),
                "recommendationCount": len(recommendations),
                "projectedRiskCount": len(risks),
                "projectedActionCount": len(actions),
                "skippedFindingCount": len(skipped_findings),
                "skippedRecommendationCount": len(skipped_recommendations),
                "skippedFindings": skipped_findings,
                "skippedRecommendations": skipped_recommendations,
            },
        )


reasoning_decision_board_adapter = ReasoningDecisionBoardAdapter()
