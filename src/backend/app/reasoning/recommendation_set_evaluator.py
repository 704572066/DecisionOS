from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.models import Finding
from app.reasoning.recommendation_generator import (
    RecommendationGenerator,
    recommendation_generator,
)
from app.reasoning.recommendation_lifecycle import (
    RecommendationLifecycleManager,
)
from app.reasoning.recommendation_models import (
    RecommendationSet,
)
from app.reasoning.recommendation_repository import (
    RecommendationRepository,
)


@dataclass
class RecommendationSetEvaluationDiagnostics:
    findingCount: int = 0
    generatedCount: int = 0
    activeRecommendationCount: int = 0
    obsoleteCount: int = 0
    skippedFindingCount: int = 0
    generationDiagnostics: dict[str, Any] = field(
        default_factory=dict
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "findingCount": self.findingCount,
            "generatedCount": self.generatedCount,
            "activeRecommendationCount": self.activeRecommendationCount,
            "obsoleteCount": self.obsoleteCount,
            "skippedFindingCount": self.skippedFindingCount,
            "generationDiagnostics": dict(
                self.generationDiagnostics
            ),
        }


class RecommendationSetEvaluator:
    """
    Execute one complete recommendation cycle.

    Pipeline:

        Finding[]
            ↓
        RecommendationGenerator
            ↓
        generated Recommendation[]
            ↓
        RecommendationLifecycleManager
            ↓
        meeting-scoped RecommendationRepository
            ↓
        RecommendationSet

    Responsibilities:
    - generate recommendations from current Findings
    - open/update/reopen recommendations generated this cycle
    - mark recommendations that disappear this cycle as obsolete
    - preserve repository identity across reasoning cycles

    The generator remains deterministic and business-field agnostic.
    """

    def __init__(
        self,
        *,
        repository: RecommendationRepository | None = None,
        generator: RecommendationGenerator | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else RecommendationRepository()
        )

        self.generator = (
            generator
            if generator is not None
            else recommendation_generator
        )

        self.lifecycle = RecommendationLifecycleManager(
            self.repository
        )

    def evaluate(
        self,
        *,
        meeting_id: str,
        context_id: str,
        findings: list[Finding],
    ) -> RecommendationSet:
        diagnostics = RecommendationSetEvaluationDiagnostics(
            findingCount=len(findings)
        )

        previous = list(
            self.repository.list(
                meeting_id
            )
        )

        generated_set = self.generator.generate(
            meeting_id=meeting_id,
            context_id=context_id,
            findings=findings,
        )

        generation_diagnostics = dict(
            generated_set.diagnostics
            or {}
        )

        diagnostics.generatedCount = len(
            generated_set.recommendations
        )
        diagnostics.skippedFindingCount = int(
            generation_diagnostics.get(
                "skippedFindingCount",
                0,
            )
        )
        diagnostics.generationDiagnostics = (
            generation_diagnostics
        )

        active_fingerprints: set[str] = set()

        for recommendation in generated_set.recommendations:
            active_fingerprints.add(
                recommendation.fingerprint
            )

            self.lifecycle.evaluate(
                meeting_id,
                recommendation,
                True,
            )

        for existing in previous:
            if (
                existing.fingerprint
                in active_fingerprints
            ):
                continue

            before_status = existing.status

            updated = self.lifecycle.evaluate(
                meeting_id,
                existing,
                False,
            )

            if (
                updated is not None
                and before_status != "obsolete"
                and updated.status == "obsolete"
            ):
                diagnostics.obsoleteCount += 1

        current = list(
            self.repository.list(
                meeting_id
            )
        )

        diagnostics.activeRecommendationCount = sum(
            1
            for recommendation in current
            if recommendation.status != "obsolete"
        )

        return RecommendationSet(
            meetingId=meeting_id,
            contextId=context_id,
            recommendations=current,
            diagnostics=diagnostics.as_dict(),
        )


recommendation_set_evaluator = RecommendationSetEvaluator()
