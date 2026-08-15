from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.reasoning.models import Finding
from app.reasoning.recommendation_models import (
    Recommendation,
    RecommendationSet,
)


@dataclass
class RecommendationGenerationDiagnostics:
    findingCount: int = 0
    activeFindingCount: int = 0
    recommendationCount: int = 0
    skippedFindingCount: int = 0

    skippedFindings: list[dict[str, Any]] = field(
        default_factory=list
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "findingCount": self.findingCount,
            "activeFindingCount": self.activeFindingCount,
            "recommendationCount": self.recommendationCount,
            "skippedFindingCount": self.skippedFindingCount,
            "skippedFindings": list(
                self.skippedFindings
            ),
        }


class RecommendationGenerator:
    """
    Deterministic Finding -> Recommendation generator.

    This component performs structural adaptation only.

    It does NOT:
        - call an LLM
        - understand business-specific fields
        - interpret policy text again
        - invent thresholds
        - perform retrieval

    Input:

        Finding

    Output:

        Recommendation

    The Finding already contains the result of reasoning. This layer
    converts that result into a machine-readable next-action proposal.
    """

    ACTIVE_FINDING_STATUSES = {
        "open",
        "updated",
        "reopened",
    }

    def generate(
        self,
        *,
        meeting_id: str,
        context_id: str,
        findings: list[Finding],
    ) -> RecommendationSet:

        diagnostics = RecommendationGenerationDiagnostics(
            findingCount=len(findings)
        )

        recommendations: list[Recommendation] = []

        for finding in findings:

            if (
                finding.status
                not in self.ACTIVE_FINDING_STATUSES
            ):
                diagnostics.skippedFindingCount += 1

                diagnostics.skippedFindings.append(
                    {
                        "findingId": finding.id,
                        "status": finding.status,
                        "reason": "finding_not_active",
                    }
                )

                continue

            diagnostics.activeFindingCount += 1

            recommendation = self._from_finding(
                meeting_id=meeting_id,
                finding=finding,
            )

            if recommendation is None:
                diagnostics.skippedFindingCount += 1

                diagnostics.skippedFindings.append(
                    {
                        "findingId": finding.id,
                        "status": finding.status,
                        "reason": (
                            "unsupported_finding_structure"
                        ),
                    }
                )

                continue

            recommendations.append(
                recommendation
            )

        diagnostics.recommendationCount = len(
            recommendations
        )

        return RecommendationSet(
            meetingId=meeting_id,
            contextId=context_id,
            recommendations=recommendations,
            diagnostics=diagnostics.as_dict(),
        )

    def _from_finding(
        self,
        *,
        meeting_id: str,
        finding: Finding,
    ) -> Recommendation | None:

        attributes = dict(
            finding.attributes or {}
        )

        operand = attributes.get("operand")

        if not isinstance(
            operand,
            dict,
        ):
            operand = None

        recommendation_type = (
            self._recommendation_type(
                finding,
                operand,
            )
        )

        action = self._action(
            finding,
            operand,
        )

        if not action:
            return None

        title = self._title(
            finding,
            operand,
        )

        fingerprint = (
            self._fingerprint(
                finding=finding,
                recommendation_type=(
                    recommendation_type
                ),
                operand=operand,
            )
        )

        recommendation_attributes = {
            "findingType": finding.type,
            "findingStatus": finding.status,
            "findingFingerprint": (
                finding.fingerprint
            ),
        }

        constraint_id = attributes.get(
            "constraintId"
        )

        if constraint_id:
            recommendation_attributes[
                "constraintId"
            ] = constraint_id

        if operand:
            recommendation_attributes[
                "recommendedSubject"
            ] = operand.get(
                "subject",
                "",
            )

            recommendation_attributes[
                "recommendedOperator"
            ] = operand.get(
                "operator",
                "",
            )

            recommendation_attributes[
                "recommendedExpectedValue"
            ] = operand.get(
                "expectedValue"
            )

            recommendation_attributes[
                "recommendedSource"
            ] = operand.get(
                "source",
                "either",
            )

        return Recommendation(
            id=self._recommendation_id(
                fingerprint
            ),

            meetingId=meeting_id,

            findingId=finding.id,

            type=recommendation_type,

            status="open",

            domain=finding.domain,

            subject=finding.subject,

            title=title,

            summary=finding.summary,

            action=action,

            priority=self._priority(
                finding.severity
            ),

            confidence=finding.confidence,

            sourceIds=list(
                finding.sourceIds
            ),

            evidence=list(
                finding.evidence
            ),

            attributes=(
                recommendation_attributes
            ),

            reasonCode=(
                f"finding:{finding.reasonCode}"
                if finding.reasonCode
                else f"finding:{finding.id}"
            ),

            fingerprint=fingerprint,
        )

    @staticmethod
    def _recommendation_type(
        finding: Finding,
        operand: dict[str, Any] | None,
    ) -> str:
        """
        Map generic Finding semantics to generic recommendation types.

        This mapping knows Finding taxonomy only. It does not know
        business fields.
        """

        if finding.type == "dependency":
            return "action"

        if finding.type == "conflict":
            return "clarification"

        if finding.type == "gap":
            return "clarification"

        if finding.type == "deviation":
            return "action"

        if finding.type == "risk":
            return "action"

        return "action"

    @staticmethod
    def _title(
        finding: Finding,
        operand: dict[str, Any] | None,
    ) -> str:

        if operand:
            operand_subject = str(
                operand.get("subject")
                or ""
            ).strip()

            if operand_subject:
                if finding.type == "dependency":
                    return (
                        f"完成必要条件："
                        f"{operand_subject}"
                    )

                if finding.type == "conflict":
                    return (
                        f"确认冲突条件："
                        f"{operand_subject}"
                    )

                if finding.type == "gap":
                    return (
                        f"补充必要信息："
                        f"{operand_subject}"
                    )

        if finding.type == "gap":
            return (
                f"补充或确认："
                f"{finding.subject}"
            )

        if finding.type == "conflict":
            return (
                f"处理冲突："
                f"{finding.subject}"
            )

        if finding.type == "deviation":
            return (
                f"处理偏差："
                f"{finding.subject}"
            )

        if finding.type == "risk":
            return (
                f"处理风险："
                f"{finding.subject}"
            )

        return finding.title

    @staticmethod
    def _action(
        finding: Finding,
        operand: dict[str, Any] | None,
    ) -> str:

        if operand:
            operand_subject = str(
                operand.get("subject")
                or ""
            ).strip()

            operand_operator = str(
                operand.get("operator")
                or ""
            ).strip()

            expected_value = operand.get(
                "expectedValue"
            )

            if operand_subject:

                if operand_operator == "exists":
                    return (
                        f"在继续当前决策前，"
                        f"确认并完成 "
                        f"{operand_subject}。"
                    )

                if operand_operator == "missing":
                    return (
                        f"确认 "
                        f"{operand_subject} "
                        f"当前是否应保持缺失状态。"
                    )

                if expected_value is not None:
                    return (
                        f"确认 "
                        f"{operand_subject} "
                        f"满足条件 "
                        f"{operand_operator} "
                        f"{expected_value}。"
                    )

                return (
                    f"确认并处理相关条件 "
                    f"{operand_subject}。"
                )

        if finding.type == "gap":
            return (
                f"补充或确认 "
                f"{finding.subject} "
                f"后再继续当前决策。"
            )

        if finding.type == "conflict":
            return (
                f"确认 "
                f"{finding.subject} "
                f"的冲突条件，并在继续决策前完成处理。"
            )

        if finding.type == "deviation":
            return (
                f"复核 "
                f"{finding.subject} "
                f"当前状态与既定要求的偏差。"
            )

        if finding.type == "risk":
            return (
                f"评估并处理 "
                f"{finding.subject} "
                f"相关风险后再继续当前决策。"
            )

        if finding.type == "dependency":
            return (
                f"确认 "
                f"{finding.subject} "
                f"依赖的必要条件已满足。"
            )

        return ""

    @staticmethod
    def _priority(
        severity: str,
    ) -> str:

        if severity in {
            "low",
            "medium",
            "high",
            "critical",
        }:
            return severity

        return "medium"

    @staticmethod
    def _fingerprint(
        *,
        finding: Finding,
        recommendation_type: str,
        operand: dict[str, Any] | None,
    ) -> str:

        recommended_subject = ""

        if operand:
            recommended_subject = str(
                operand.get("subject")
                or ""
            )

        return ":".join(
            [
                recommendation_type,
                finding.domain or "_",
                finding.subject or "_",
                recommended_subject or "_",
                finding.fingerprint
                or finding.id,
            ]
        )

    @staticmethod
    def _recommendation_id(
        fingerprint: str,
    ) -> str:

        digest = hashlib.sha1(
            fingerprint.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

        return (
            f"recommendation-{digest}"
        )


recommendation_generator = RecommendationGenerator()