from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.constraint_evaluator import (
    ConstraintEvaluator,
    constraint_evaluator,
)
from app.reasoning.context import (
    EvaluationConstraint,
    EvaluationContext,
)
from app.reasoning.models import Finding


@dataclass
class NormativeBoundaryDiagnostics:
    inputGeneralFindingCount: int = 0
    outputGeneralFindingCount: int = 0
    suppressedGeneralFindingCount: int = 0
    suppressedGeneralFindings: list[dict[str, Any]] = field(
        default_factory=list
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "inputGeneralFindingCount": self.inputGeneralFindingCount,
            "outputGeneralFindingCount": self.outputGeneralFindingCount,
            "suppressedGeneralFindingCount": (
                self.suppressedGeneralFindingCount
            ),
            "suppressedGeneralFindings": list(
                self.suppressedGeneralFindings
            ),
        }


@dataclass
class NormativeBoundaryResult:
    findings: list[Finding] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


class NormativeBoundaryGuard:
    """
    Deterministic boundary between enterprise constraints and General
    Reasoner findings.

    General Reasoner may use enterprise policy as context, but it must not
    reinterpret a compiled normative trigger. Once policy text has become an
    EvaluationConstraint, the Constraint Engine is authoritative for whether
    that rule applies to the current EvaluationContext.

    The guard is intentionally narrow. It only intervenes when a General
    finding is clearly linked to a structured enterprise constraint through
    policy provenance and the finding is making a normative/missing-condition
    claim about that constraint.
    """

    NORMATIVE_TERMS = (
        "必须",
        "要求",
        "合规",
        "不合规",
        "违反",
        "触发",
        "政策",
        "规则",
        "required",
        "requirement",
        "must",
        "compliance",
        "violate",
        "trigger",
        "policy",
        "rule",
    )

    def __init__(
        self,
        *,
        evaluator: ConstraintEvaluator | None = None,
    ) -> None:
        self.evaluator = (
            evaluator
            if evaluator is not None
            else constraint_evaluator
        )

    def apply(
        self,
        *,
        context: EvaluationContext,
        constraints: list[EvaluationConstraint],
        enterprise_findings: list[Finding],
        general_findings: list[Finding],
    ) -> NormativeBoundaryResult:
        diagnostics = NormativeBoundaryDiagnostics(
            inputGeneralFindingCount=len(general_findings)
        )

        active_constraint_ids = {
            str(
                (finding.attributes or {}).get(
                    "constraintId",
                    "",
                )
            )
            for finding in enterprise_findings
            if finding.status != "resolved"
            and (finding.attributes or {}).get("constraintId")
        }

        output: list[Finding] = []

        for finding in general_findings:
            suppression = self._suppression_reason(
                context=context,
                constraints=constraints,
                active_constraint_ids=active_constraint_ids,
                finding=finding,
            )

            if suppression is None:
                output.append(finding)
                continue

            reason, details = suppression

            diagnostics.suppressedGeneralFindingCount += 1
            diagnostics.suppressedGeneralFindings.append(
                {
                    "findingId": finding.id,
                    "fingerprint": finding.fingerprint,
                    "reason": reason,
                    **details,
                }
            )

        diagnostics.outputGeneralFindingCount = len(output)

        return NormativeBoundaryResult(
            findings=output,
            diagnostics=diagnostics.as_dict(),
        )

    def _suppression_reason(
        self,
        *,
        context: EvaluationContext,
        constraints: list[EvaluationConstraint],
        active_constraint_ids: set[str],
        finding: Finding,
    ) -> tuple[str, dict[str, Any]] | None:
        if not self._is_general(finding):
            return None

        linked = self._linked_constraints(
            finding,
            constraints,
        )

        if not linked:
            return None

        for constraint in linked:
            # The authoritative evaluator tells us whether the structured
            # rule actually fires in the current state.
            evaluation = self.evaluator.evaluate(
                context,
                constraint,
            )

            primary_reason = str(
                (evaluation.diagnostics or {}).get(
                    "reason",
                    "",
                )
            )

            # If the primary trigger itself is false, General Reasoner may
            # not invent a requirement downstream of that trigger.
            if primary_reason == "primary_condition_not_triggered":
                return (
                    "normative_precondition_not_satisfied",
                    {
                        "constraintId": constraint.id,
                        "constraintSubject": constraint.subject,
                        "operator": constraint.operator,
                        "expectedValue": constraint.expectedValue,
                    },
                )

            # When the structured constraint is already represented by an
            # active enterprise Finding, Enterprise Reasoner owns the issue.
            if constraint.id in active_constraint_ids:
                return (
                    "normative_issue_already_covered",
                    {
                        "constraintId": constraint.id,
                    },
                )

            # If the primary condition applies but the full constraint did
            # not trigger, the required operand/condition is already
            # satisfied. A General missing-information warning would be a
            # false normative warning.
            if (
                constraint.operand is not None
                and not evaluation.triggered
                and primary_reason == "operand_condition_satisfied"
            ):
                return (
                    "normative_requirement_already_satisfied",
                    {
                        "constraintId": constraint.id,
                        "operandSubject": constraint.operand.subject,
                    },
                )

        return None

    @classmethod
    def _linked_constraints(
        cls,
        finding: Finding,
        constraints: list[EvaluationConstraint],
    ) -> list[EvaluationConstraint]:
        finding_sources = {
            str(item)
            for item in finding.sourceIds
            if item
        }

        if not finding_sources:
            return []

        candidates = [
            constraint
            for constraint in constraints
            if finding_sources.intersection(
                str(item)
                for item in constraint.sourceIds
                if item
            )
        ]

        if not candidates:
            return []

        attributes = dict(finding.attributes or {})
        general_type = str(
            attributes.get("generalFindingType")
            or ""
        )

        text = cls._normalize(
            " ".join(
                [
                    finding.subject,
                    finding.title,
                    finding.summary,
                    str(attributes.get("suggestedAction") or ""),
                ]
            )
        )

        looks_normative = (
            general_type == "missing_information"
            or any(
                cls._normalize(term) in text
                for term in cls.NORMATIVE_TERMS
            )
        )

        if not looks_normative:
            return []

        scored: list[tuple[int, EvaluationConstraint]] = []

        for constraint in candidates:
            score = cls._constraint_link_score(
                finding,
                constraint,
            )
            if score > 0:
                scored.append((score, constraint))

        if scored:
            best = max(score for score, _ in scored)
            return [
                constraint
                for score, constraint in scored
                if score == best
            ]

        # Conservative fallback: when there is exactly one dependency-like
        # constraint from the cited policy source, a normative
        # missing-information finding almost certainly refers to it.
        dependency_candidates = [
            constraint
            for constraint in candidates
            if constraint.operand is not None
        ]

        if (
            general_type == "missing_information"
            and len(dependency_candidates) == 1
        ):
            return dependency_candidates

        return []

    @classmethod
    def _constraint_link_score(
        cls,
        finding: Finding,
        constraint: EvaluationConstraint,
    ) -> int:
        subject = cls._normalize(finding.subject)
        primary = cls._normalize(constraint.subject)
        operand = cls._normalize(
            constraint.operand.subject
            if constraint.operand is not None
            else ""
        )

        finding_text = cls._normalize(
            " ".join(
                [
                    finding.subject,
                    finding.title,
                    finding.summary,
                    str(
                        (finding.attributes or {}).get(
                            "suggestedAction",
                            "",
                        )
                    ),
                ]
            )
        )

        constraint_text = cls._normalize(
            " ".join(
                [
                    constraint.subject,
                    constraint.title,
                    constraint.description,
                    (
                        constraint.operand.subject
                        if constraint.operand is not None
                        else ""
                    ),
                ]
            )
        )

        if subject and operand and subject == operand:
            return 100

        if subject and primary and subject == primary:
            return 90

        # Human-facing subjects such as "付款周期" can be linked to a
        # machine operand such as paymentTermAssessment because the compiled
        # constraint title/description preserves the policy language.
        if (
            subject
            and len(subject) >= 2
            and subject in constraint_text
        ):
            return 80

        if operand and operand in finding_text:
            return 75

        if primary and primary in finding_text:
            return 60

        return 0

    @staticmethod
    def _is_general(finding: Finding) -> bool:
        return (
            (finding.attributes or {}).get(
                "reasoningSource"
            )
            == "general"
        )

    @staticmethod
    def _normalize(value: Any) -> str:
        return "".join(
            str(value or "").lower().split()
        )


normative_boundary_guard = NormativeBoundaryGuard()
