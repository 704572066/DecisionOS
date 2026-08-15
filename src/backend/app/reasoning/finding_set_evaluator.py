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
from app.reasoning.finding_lifecycle import (
    FindingLifecycleManager,
)
from app.reasoning.finding_repository import (
    FindingRepository,
)
from app.reasoning.models import (
    Finding,
    FindingSet,
)


@dataclass
class FindingSetEvaluationDiagnostics:
    constraintCount: int = 0
    triggeredCount: int = 0
    activeFindingCount: int = 0
    resolvedCount: int = 0
    evaluationErrors: list[dict[str, Any]] = field(
        default_factory=list
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "constraintCount": self.constraintCount,
            "triggeredCount": self.triggeredCount,
            "activeFindingCount": self.activeFindingCount,
            "resolvedCount": self.resolvedCount,
            "evaluationErrorCount": len(
                self.evaluationErrors
            ),
            "evaluationErrors": list(
                self.evaluationErrors
            ),
        }


class FindingSetEvaluator:
    """
    Execute one complete reasoning cycle.

    Pipeline:

        EvaluationContext
              +
        EvaluationConstraint[]
              ↓
        ConstraintEvaluator
              ↓
        current triggered findings
              ↓
        FindingLifecycleManager
              ↓
        meeting-scoped FindingRepository
              ↓
        FindingSet

    Responsibilities:
    - evaluate all constraints
    - open/update/reopen active findings
    - resolve findings that disappeared this cycle
    - return all meeting-scoped findings

    Non-responsibilities:
    - compile natural-language policy
    - evaluate business-specific rules
    - persist to database
    - adapt Findings into DecisionBoard UI models
    """

    def __init__(
        self,
        *,
        repository: FindingRepository | None = None,
        constraint_evaluator_instance: ConstraintEvaluator | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else FindingRepository()
        )

        self.constraint_evaluator = (
            constraint_evaluator_instance
            if constraint_evaluator_instance is not None
            else constraint_evaluator
        )

        self.lifecycle = FindingLifecycleManager(
            self.repository
        )

    def evaluate(
        self,
        context: EvaluationContext,
        constraints: list[EvaluationConstraint],
    ) -> FindingSet:
        diagnostics = (
            FindingSetEvaluationDiagnostics(
                constraintCount=len(constraints)
            )
        )

        meeting_id = context.meetingId

        #
        # Snapshot previous meeting findings BEFORE processing
        # the current cycle.
        #
        previous_findings = list(
            self.repository.list(
                meeting_id
            )
        )

        active_fingerprints: set[str] = set()

        #
        # 1. Evaluate every current constraint.
        #
        for constraint in constraints:
            try:
                result = (
                    self.constraint_evaluator.evaluate(
                        context,
                        constraint,
                    )
                )
            except Exception as exc:
                diagnostics.evaluationErrors.append(
                    {
                        "constraintId": (
                            constraint.id
                        ),
                        "error": str(exc),
                    }
                )
                continue

            if (
                not result.triggered
                or result.finding is None
            ):
                continue

            diagnostics.triggeredCount += 1

            finding = result.finding

            active_fingerprints.add(
                finding.fingerprint
            )

            #
            # OPEN / UPDATE / REOPEN
            #
            self.lifecycle.evaluate(
                meeting_id,
                finding,
                True,
            )

        #
        # 2. Resolve findings that existed before this cycle
        #    but were not triggered now.
        #
        # Important:
        # only touch findings belonging to this meeting.
        #
        for existing in previous_findings:
            if (
                existing.status == "resolved"
            ):
                continue

            if (
                existing.fingerprint
                in active_fingerprints
            ):
                continue

            resolved = (
                self.lifecycle.evaluate(
                    meeting_id,
                    existing,
                    False,
                )
            )

            if (
                resolved is not None
                and resolved.status == "resolved"
            ):
                diagnostics.resolvedCount += 1

        current_findings = list(
            self.repository.list(
                meeting_id
            )
        )

        diagnostics.activeFindingCount = sum(
            1
            for finding in current_findings
            if finding.status != "resolved"
        )

        return FindingSet(
            meetingId=context.meetingId,
            contextId=context.contextId,
            findings=current_findings,
            diagnostics=diagnostics.as_dict(),
        )


finding_set_evaluator = FindingSetEvaluator()