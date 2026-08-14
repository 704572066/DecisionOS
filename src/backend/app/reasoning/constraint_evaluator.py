from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.reasoning.context import (
    EvaluationConstraint,
    EvaluationContext,
    EvaluationSubject,
)
from app.reasoning.models import (
    Finding,
    FindingEvidence,
)
from app.reasoning.operator_evaluator import (
    OperatorEvaluationResult,
    OperatorEvaluator,
    operator_evaluator,
)
from app.reasoning.subject_resolver import (
    SubjectResolver,
    subject_resolver,
)


@dataclass
class ConstraintEvaluationResult:
    """
    Result of evaluating one EvaluationConstraint.

    E3 evaluates one constraint only.

    Finding lifecycle management such as:
        OPEN
        UPDATED
        RESOLVED
        REOPENED

    belongs to E4.
    """

    constraintId: str

    triggered: bool = False

    finding: Finding | None = None

    primaryResult: OperatorEvaluationResult | None = None

    operandResult: OperatorEvaluationResult | None = None

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )


class ConstraintEvaluator:
    """
    Execute one generic EvaluationConstraint.

    This evaluator contains no business field knowledge.

    It does NOT know:
        discountPercent
        paymentTermDays
        legalApproval
        goLiveDate
        paymentTermAssessment

    It only understands the generic constraint DSL.
    """

    #
    # These statuses describe semantic objects that are no longer
    # current active positions.
    #
    # This is lifecycle semantics, not business-specific logic.
    #
    INACTIVE_STATUSES = {
        "rejected",
        "withdrawn",
    }

    RELATIONAL_OPERATORS = {
        "requires",
        "depends_on",
        "conflicts_with",
    }

    def __init__(
        self,
        *,
        resolver: SubjectResolver | None = None,
        evaluator: OperatorEvaluator | None = None,
    ) -> None:
        self.resolver = (
            resolver
            if resolver is not None
            else subject_resolver
        )

        self.operator_evaluator = (
            evaluator
            if evaluator is not None
            else operator_evaluator
        )

    def evaluate(
        self,
        context: EvaluationContext,
        constraint: EvaluationConstraint,
    ) -> ConstraintEvaluationResult:

        #
        # 1. Resolve primary subject.
        #
        primary_resolution = self.resolver.resolve(
            context,
            domain=constraint.domain,
            subject=constraint.subject,
            source=constraint.subjectSource,
            actor=constraint.actor,
        )

        active_primary = self._active_subjects(
            primary_resolution.matches
        )

        #
        # 2. Evaluate primary condition.
        #
        if (
            constraint.operator
            in self.RELATIONAL_OPERATORS
        ):
            #
            # For pure relational rules:
            #
            #     X requires Y
            #     X depends_on Y
            #     X conflicts_with Y
            #
            # X existing is the primary trigger.
            #
            primary_result = (
                self.operator_evaluator.evaluate(
                    active_primary,
                    operator="exists",
                )
            )
        else:
            primary_result = (
                self.operator_evaluator.evaluate(
                    active_primary,
                    operator=constraint.operator,
                    expected_value=constraint.expectedValue,
                )
            )

        primary_triggered = (
            self._primary_triggered(
                constraint,
                primary_result,
            )
        )

        if not primary_triggered:
            return ConstraintEvaluationResult(
                constraintId=constraint.id,
                triggered=False,
                primaryResult=primary_result,
                diagnostics={
                    "reason": (
                        "primary_condition_not_triggered"
                    ),
                    "primarySubjectCount": len(
                        active_primary
                    ),
                },
            )

        #
        # 3. No operand:
        #
        # Primary condition itself produces the Finding.
        #
        if constraint.operand is None:
            finding = self._build_finding(
                context=context,
                constraint=constraint,
                primary_result=primary_result,
                operand_result=None,
            )

            return ConstraintEvaluationResult(
                constraintId=constraint.id,
                triggered=True,
                finding=finding,
                primaryResult=primary_result,
                diagnostics={
                    "reason": (
                        "primary_condition_triggered"
                    ),
                    "primarySubjectCount": len(
                        active_primary
                    ),
                },
            )

        #
        # 4. Resolve operand.
        #
        operand = constraint.operand

        operand_resolution = self.resolver.resolve(
            context,
            domain=operand.domain,
            subject=operand.subject,
            source=operand.source,
            actor=operand.actor,
        )

        active_operand = self._active_subjects(
            operand_resolution.matches
        )

        operand_result = (
            self.operator_evaluator.evaluate(
                active_operand,
                operator=operand.operator,
                expected_value=operand.expectedValue,
            )
        )

        #
        # 5. Determine whether operand relationship actually causes
        #    a Finding.
        #
        finding_triggered = (
            self._operand_triggers_finding(
                constraint,
                operand_result,
            )
        )

        if not finding_triggered:
            return ConstraintEvaluationResult(
                constraintId=constraint.id,
                triggered=False,
                primaryResult=primary_result,
                operandResult=operand_result,
                diagnostics={
                    "reason": (
                        "operand_condition_satisfied"
                    ),
                    "primarySubjectCount": len(
                        active_primary
                    ),
                    "operandSubjectCount": len(
                        active_operand
                    ),
                },
            )

        finding = self._build_finding(
            context=context,
            constraint=constraint,
            primary_result=primary_result,
            operand_result=operand_result,
        )

        return ConstraintEvaluationResult(
            constraintId=constraint.id,
            triggered=True,
            finding=finding,
            primaryResult=primary_result,
            operandResult=operand_result,
            diagnostics={
                "reason": (
                    "constraint_triggered"
                ),
                "primarySubjectCount": len(
                    active_primary
                ),
                "operandSubjectCount": len(
                    active_operand
                ),
            },
        )

    @classmethod
    def _active_subjects(
        cls,
        subjects: list[EvaluationSubject],
    ) -> list[EvaluationSubject]:
        """
        Remove semantic positions that are explicitly no longer active.

        Example:

            us / discount=15 / rejected

        must not trigger a CURRENT enterprise-policy evaluation.

        We intentionally do not filter:
            proposed
            pending
            confirmed
            accepted
            empty status

        because their meaning depends on which state surface the
        constraint selected.
        """

        return [
            subject
            for subject in subjects
            if subject.status
            not in cls.INACTIVE_STATUSES
        ]

    @staticmethod
    def _primary_triggered(
        constraint: EvaluationConstraint,
        result: OperatorEvaluationResult,
    ) -> bool:
        """
        Interpret evaluationMode.

        on_match:
            matching the condition activates the rule.

        on_mismatch:
            the condition describes what SHOULD hold;
            failure activates the rule.

        Fail closed when values are not comparable.
        """

        if not result.comparable:
            return False

        if constraint.evaluationMode == "on_match":
            return result.matched

        if constraint.evaluationMode == "on_mismatch":
            return not result.matched

        return False

    @classmethod
    def _operand_triggers_finding(
        cls,
        constraint: EvaluationConstraint,
        operand_result: OperatorEvaluationResult,
    ) -> bool:
        """
        Evaluate the relationship between primary trigger and operand.

        Dependency semantics:

            primary trigger occurs
                +
            required operand condition is NOT satisfied
                ↓
            Finding

        Conflict semantics:

            primary trigger occurs
                +
            operand condition IS satisfied
                ↓
            Finding
        """

        if not operand_result.comparable:
            #
            # Unknown/uncomparable is not silently interpreted as
            # violation.
            #
            return False

        if (
            constraint.operator
            == "conflicts_with"
            or constraint.findingType
            == "conflict"
        ):
            return operand_result.matched

        #
        # requires / depends_on / dependency-style trigger:
        #
        # The operand describes the condition that must hold.
        #
        return not operand_result.matched

    def _build_finding(
        self,
        *,
        context: EvaluationContext,
        constraint: EvaluationConstraint,
        primary_result: OperatorEvaluationResult,
        operand_result: OperatorEvaluationResult | None,
    ) -> Finding:

        fingerprint = (
            self._fingerprint(
                constraint
            )
        )

        evidence = self._finding_evidence(
            context=context,
            constraint=constraint,
            primary_result=primary_result,
            operand_result=operand_result,
        )

        source_ids = list(
            dict.fromkeys(
                [
                    *constraint.sourceIds,
                    *[
                        item.sourceId
                        for item in evidence
                        if item.sourceId
                    ],
                ]
            )
        )

        title = (
            constraint.title.strip()
            or self._default_title(
                constraint
            )
        )

        summary = (
            constraint.description.strip()
            or self._default_summary(
                constraint
            )
        )

        return Finding(
            id=self._finding_id(
                fingerprint
            ),

            type=constraint.findingType,

            status="open",

            domain=constraint.domain,

            subject=constraint.subject,

            title=title,

            summary=summary,

            severity=constraint.severity,

            confidence=self._finding_confidence(
                evidence
            ),

            sourceIds=source_ids,

            evidence=evidence,

            attributes={
                "constraintId": constraint.id,

                "operator": (
                    constraint.operator
                ),

                "expectedValue": (
                    constraint.expectedValue
                ),

                "evaluationMode": (
                    constraint.evaluationMode
                ),

                "operand": (
                    constraint.operand.model_dump(
                        mode="json"
                    )
                    if constraint.operand
                    else None
                ),
            },

            reasonCode=(
                f"constraint:{constraint.id}"
            ),

            fingerprint=fingerprint,
        )

    @staticmethod
    def _finding_evidence(
        *,
        context: EvaluationContext,
        constraint: EvaluationConstraint,
        primary_result: OperatorEvaluationResult,
        operand_result: OperatorEvaluationResult | None,
    ) -> list[FindingEvidence]:

        output: list[FindingEvidence] = []

        #
        # For on_match:
        # matched primary subjects caused the trigger.
        #
        # For on_mismatch:
        # unmatched subjects explain the violation.
        #
        primary_subjects = (
            primary_result.matchedSubjects
            if constraint.evaluationMode
            == "on_match"
            else primary_result.unmatchedSubjects
        )

        for subject in primary_subjects:
            output.append(
                ConstraintEvaluator._subject_evidence(
                    subject
                )
            )

        #
        # If an operand matched and that match is relevant
        # (e.g. conflicts_with), preserve it.
        #
        if operand_result is not None:
            for subject in (
                operand_result.matchedSubjects
            ):
                output.append(
                    ConstraintEvaluator._subject_evidence(
                        subject
                    )
                )

        #
        # Add enterprise knowledge provenance.
        #
        knowledge_by_id = {
            item.id: item
            for item in context.knowledge
        }

        for source_id in constraint.sourceIds:
            knowledge = (
                knowledge_by_id.get(
                    source_id
                )
            )

            if knowledge is None:
                continue

            source_type = (
                ConstraintEvaluator._finding_source_type(
                    knowledge.sourceType
                )
            )

            output.append(
                FindingEvidence(
                    sourceType=source_type,
                    sourceId=knowledge.id,
                    title=knowledge.title,
                    summary=(
                        knowledge.summary
                        or knowledge.content
                    ),
                    confidence=knowledge.score,
                    metadata={
                        "knowledgeSourceType": (
                            knowledge.sourceType
                        )
                    },
                )
            )

        #
        # Deduplicate exact provenance.
        #
        deduped: list[FindingEvidence] = []
        seen: set[tuple] = set()

        for item in output:
            key = (
                item.sourceType,
                item.sourceId,
                item.field,
                repr(item.value),
                item.actor,
            )

            if key in seen:
                continue

            seen.add(key)
            deduped.append(item)

        return deduped

    @staticmethod
    def _subject_evidence(
        subject: EvaluationSubject,
    ) -> FindingEvidence:
        return FindingEvidence(
            sourceType=(
                "decision_state"
                if subject.sourceType
                == "decision_state"
                else "semantic_state"
            ),

            sourceId=subject.sourceId,

            summary=subject.sourceText,

            field=subject.field,

            value=subject.value,

            actor=subject.actor,

            confidence=subject.confidence,

            metadata={
                "domain": subject.domain,
                "role": subject.role,
                "status": subject.status,
                "relation": subject.relation,
                **dict(
                    subject.metadata or {}
                ),
            },
        )

    @staticmethod
    def _finding_source_type(
        value: str,
    ) -> str:
        allowed = {
            "semantic_state",
            "decision_state",
            "policy",
            "decision",
            "document",
            "crm",
            "runtime",
            "knowledge",
            "other",
        }

        return (
            value
            if value in allowed
            else "other"
        )

    @staticmethod
    def _finding_confidence(
        evidence: list[FindingEvidence],
    ) -> float:
        if not evidence:
            return 0.5

        values = [
            item.confidence
            for item in evidence
        ]

        return max(
            0.0,
            min(
                1.0,
                sum(values)
                / len(values),
            ),
        )

    @staticmethod
    def _fingerprint(
        constraint: EvaluationConstraint,
    ) -> str:
        operand_subject = (
            constraint.operand.subject
            if constraint.operand
            else ""
        )

        return ":".join(
            [
                constraint.findingType,
                constraint.domain or "_",
                constraint.subject,
                constraint.operator,
                operand_subject,
                constraint.id,
            ]
        )

    @staticmethod
    def _finding_id(
        fingerprint: str,
    ) -> str:
        digest = hashlib.sha1(
            fingerprint.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

        return (
            f"finding-{digest}"
        )

    @staticmethod
    def _default_title(
        constraint: EvaluationConstraint,
    ) -> str:
        return (
            f"{constraint.subject} "
            f"触发企业约束"
        )

    @staticmethod
    def _default_summary(
        constraint: EvaluationConstraint,
    ) -> str:
        if constraint.operand:
            return (
                f"{constraint.subject} "
                f"{constraint.operator} "
                f"{constraint.expectedValue}; "
                f"相关条件 "
                f"{constraint.operand.subject} "
                f"未满足当前约束要求。"
            )

        return (
            f"{constraint.subject} "
            f"未满足企业约束要求。"
        )


constraint_evaluator = ConstraintEvaluator()