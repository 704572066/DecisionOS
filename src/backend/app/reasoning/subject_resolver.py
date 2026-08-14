from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.reasoning.context import (
    ConstraintSubjectSource,
    EvaluationContext,
    EvaluationSubject,
)


@dataclass
class SubjectResolution:
    """
    Result of resolving one logical subject from EvaluationContext.

    We intentionally return full EvaluationSubject objects rather than
    raw values so downstream reasoning preserves:

    - actor
    - role
    - status
    - sourceType
    - sourceId
    - confidence
    - provenance
    """

    domain: str
    subject: str
    source: ConstraintSubjectSource

    matches: list[EvaluationSubject] = field(
        default_factory=list
    )

    @property
    def found(self) -> bool:
        return bool(self.matches)

    @property
    def count(self) -> int:
        return len(self.matches)

    @property
    def values(self) -> list:
        return [
            item.value
            for item in self.matches
        ]


class SubjectResolver:
    """
    Generic resolver for EvaluationContext subjects.

    It knows nothing about business fields.

    It does NOT know:
    - discountPercent
    - paymentTermDays
    - goLiveDate
    - legalApproval
    - scopeInclusion

    Resolution is structural only:

        domain
        +
        subject
        +
        source
        +
        optional actor
    """

    def resolve(
        self,
        context: EvaluationContext,
        *,
        domain: str = "",
        subject: str,
        source: ConstraintSubjectSource = "either",
        actor: str = "",
    ) -> SubjectResolution:
        candidates = self._source_candidates(
            context,
            source=source,
        )

        matches = [
            item
            for item in candidates
            if self._matches(
                item,
                domain=domain,
                subject=subject,
                actor=actor,
            )
        ]

        return SubjectResolution(
            domain=domain,
            subject=subject,
            source=source,
            matches=matches,
        )

    @staticmethod
    def _source_candidates(
        context: EvaluationContext,
        *,
        source: ConstraintSubjectSource,
    ) -> list[EvaluationSubject]:
        if source == "semantic_state":
            return list(
                context.semanticSubjects
            )

        if source == "decision_state":
            return list(
                context.decisionSubjects
            )

        if source == "either":
            return SubjectResolver._merge_sources(
                context.semanticSubjects,
                context.decisionSubjects,
            )

        # Defensive fail-closed behavior.
        # Pydantic should normally prevent this branch.
        return []

    @staticmethod
    def _matches(
        item: EvaluationSubject,
        *,
        domain: str,
        subject: str,
        actor: str,
    ) -> bool:
        if item.field != subject:
            return False

        if (
            domain
            and item.domain != domain
        ):
            return False

        if (
            actor
            and item.actor != actor
        ):
            return False

        return True

    @staticmethod
    def _merge_sources(
        semantic_subjects: list[EvaluationSubject],
        decision_subjects: list[EvaluationSubject],
    ) -> list[EvaluationSubject]:
        """
        Merge the two state surfaces without destroying provenance.

        semantic_state and decision_state may legitimately contain the
        same logical field because they mean different things:

            semanticState
                participant position

            decisionState
                current effective decision

        Therefore we do NOT deduplicate merely by domain + field + value.

        Only exact duplicate source objects are collapsed.
        """

        output: list[EvaluationSubject] = []
        seen: set[tuple] = set()

        for item in [
            *semantic_subjects,
            *decision_subjects,
        ]:
            key = (
                item.sourceType,
                item.sourceId,
                item.domain,
                item.field,
                item.actor,
                item.role,
                item.status,
                repr(item.value),
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(item)

        return output


subject_resolver = SubjectResolver()