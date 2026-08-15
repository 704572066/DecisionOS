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
    """

    constraintId: str

    triggered: bool = False

    finding: Finding | None = None

    primaryResult: OperatorEvaluationResult | None = None

    operandResult: OperatorEvaluationResult | None = None

    ignoredSubjects: list[dict[str, Any]] = field(
        default_factory=list
    )

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )


class ConstraintEvaluator:

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
        # 1. Resolve primary subject
        #

        primary_resolution = self.resolver.resolve(
            context,
            domain=constraint.domain,
            subject=constraint.subject,
            source=constraint.subjectSource,
            actor=constraint.actor,
        )


        ignored_primary = [
            subject
            for subject
            in primary_resolution.matches
            if subject.status
            in self.INACTIVE_STATUSES
        ]


        active_primary = self._active_subjects(
            primary_resolution.matches
        )


        #
        # 2. Evaluate primary condition
        #

        if (
            constraint.operator
            in self.RELATIONAL_OPERATORS
        ):

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

                ignoredSubjects=(
                    self._ignored_subject_payload(
                        ignored_primary
                    )
                ),

                diagnostics={

                    "reason":
                        "primary_condition_not_triggered",

                    "primarySubjectCount":
                        len(active_primary),

                    "ignoredSubjectCount":
                        len(ignored_primary),

                    "ignoredSubjects":
                        self._ignored_subject_payload(
                            ignored_primary
                        ),
                },
            )


        #
        # 3. No operand
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

                ignoredSubjects=(
                    self._ignored_subject_payload(
                        ignored_primary
                    )
                ),

                diagnostics={

                    "reason":
                        "primary_condition_triggered",

                    "primarySubjectCount":
                        len(active_primary),

                    "ignoredSubjectCount":
                        len(ignored_primary),

                    "ignoredSubjects":
                        self._ignored_subject_payload(
                            ignored_primary
                        ),
                },
            )


        #
        # 4. Resolve operand
        #

        operand = constraint.operand


        operand_resolution = self.resolver.resolve(
            context,
            domain=operand.domain,
            subject=operand.subject,
            source=operand.source,
            actor=operand.actor,
        )


        ignored_operand = [
            subject
            for subject
            in operand_resolution.matches
            if subject.status
            in self.INACTIVE_STATUSES
        ]


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
        # 5. Determine whether operand relationship triggers Finding
        #

        finding_triggered = (
            self._operand_triggers_finding(
                constraint,
                operand_result,
            )
        )


        ignored_subjects = (
            self._ignored_subject_payload(
                [
                    *ignored_primary,
                    *ignored_operand,
                ]
            )
        )


        if not finding_triggered:

            return ConstraintEvaluationResult(
                constraintId=constraint.id,

                triggered=False,

                primaryResult=primary_result,

                operandResult=operand_result,

                ignoredSubjects=ignored_subjects,

                diagnostics={

                    "reason":
                        "operand_condition_satisfied",

                    "primarySubjectCount":
                        len(active_primary),

                    "operandSubjectCount":
                        len(active_operand),

                    "ignoredSubjectCount":
                        len(ignored_subjects),

                    "ignoredSubjects":
                        ignored_subjects,
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

            ignoredSubjects=ignored_subjects,

            diagnostics={

                "reason":
                    "constraint_triggered",

                "primarySubjectCount":
                    len(active_primary),

                "operandSubjectCount":
                    len(active_operand),

                "ignoredSubjectCount":
                    len(ignored_subjects),

                "ignoredSubjects":
                    ignored_subjects,
            },
        )


    @classmethod
    def _active_subjects(
        cls,
        subjects: list[EvaluationSubject],
    ) -> list[EvaluationSubject]:

        return [
            subject
            for subject in subjects
            if subject.status
            not in cls.INACTIVE_STATUSES
        ]


    @staticmethod
    def _ignored_subject_payload(
        subjects: list[EvaluationSubject],
    ) -> list[dict[str, Any]]:

        return [
            {
                "field": subject.field,
                "value": subject.value,
                "status": subject.status,
                "actor": subject.actor,
                "sourceId": subject.sourceId,
            }
            for subject in subjects
        ]


    @staticmethod
    def _primary_triggered(
        constraint: EvaluationConstraint,
        result: OperatorEvaluationResult,
    ) -> bool:

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

        if not operand_result.comparable:
            return False


        if (
            constraint.operator
            == "conflicts_with"
            or constraint.findingType
            == "conflict"
        ):
            return operand_result.matched


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


        return Finding(
            id=self._finding_id(
                fingerprint
            ),

            type=constraint.findingType,

            status="open",

            domain=constraint.domain,

            subject=constraint.subject,

            title=(
                constraint.title.strip()
                or self._default_title(
                    constraint
                )
            ),

            summary=(
                constraint.description.strip()
                or self._default_summary(
                    constraint
                )
            ),

            severity=constraint.severity,

            confidence=self._finding_confidence(
                evidence
            ),

            sourceIds=source_ids,

            evidence=evidence,

            attributes={
                "constraintId": constraint.id,

                "operator":
                    constraint.operator,

                "expectedValue":
                    constraint.expectedValue,

                "evaluationMode":
                    constraint.evaluationMode,

                "operand":
                    (
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


        primary_subjects = (
            primary_result.matchedSubjects
            if constraint.evaluationMode == "on_match"
            else primary_result.unmatchedSubjects
        )


        for subject in primary_subjects:
            output.append(
                ConstraintEvaluator._subject_evidence(
                    subject
                )
            )


        if operand_result is not None:

            for subject in operand_result.matchedSubjects:

                output.append(
                    ConstraintEvaluator._subject_evidence(
                        subject
                    )
                )


        knowledge_by_id = {
            item.id:item
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


            output.append(
                FindingEvidence(
                    sourceType=(
                        ConstraintEvaluator
                        ._finding_source_type(
                            knowledge.sourceType
                        )
                    ),

                    sourceId=knowledge.id,

                    title=knowledge.title,

                    summary=(
                        knowledge.summary
                        or knowledge.content
                    ),

                    confidence=knowledge.score,

                    metadata={
                        "knowledgeSourceType":
                            knowledge.sourceType
                    },
                )
            )


        deduped=[]
        seen=set()


        for item in output:

            key=(
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