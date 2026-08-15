from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.reasoning.recommendation_models import (
    Recommendation,
)

from app.reasoning.recommendation_repository import (
    RecommendationRepository,
    recommendation_repository,
)
class RecommendationLifecycleManager:
    """
    Manage Recommendation lifecycle.

    Automatic reasoning lifecycle:

        first active
            -> open

        remains active
            -> update existing Recommendation

        Finding disappears/resolves
            -> obsolete

        Finding becomes active again
            -> reopen same Recommendation

    Explicit user lifecycle:

        open -> accepted
        open/accepted -> completed
        open/accepted -> dismissed

    User states are not reset merely because another reasoning cycle
    generates the same Recommendation.
    """

    def __init__(
        self,
        repository: RecommendationRepository,
    ) -> None:
        self.repository = repository

    def evaluate(
        self,
        meeting_id: str,
        recommendation: Optional[Recommendation],
        active: bool,
    ) -> Optional[Recommendation]:

        if recommendation is None:
            return None

        existing = (
            self.repository.find_by_fingerprint(
                meeting_id,
                recommendation.fingerprint,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        #
        # First observation.
        #
        if existing is None:

            if not active:
                return None

            recommendation.status = "open"
            recommendation.firstObservedAt = now
            recommendation.updatedAt = now

            self.repository.save(
                meeting_id,
                recommendation,
            )

            return recommendation

        #
        # Finding / recommendation is active in this cycle.
        #
        if active:

            #
            # Previous occurrence disappeared and is now present again.
            #
            if existing.status == "obsolete":
                self._copy_generated_content(
                    existing,
                    recommendation,
                )

                existing.status = "open"
                existing.completedAt = None
                existing.dismissedAt = None
                existing.updatedAt = now

                self.repository.update(
                    meeting_id,
                    existing,
                )

                return existing

            #
            # Explicit user states must not be silently destroyed by
            # another reasoning cycle.
            #
            if existing.status in {
                "accepted",
                "completed",
                "dismissed",
            }:
                self._copy_generated_content(
                    existing,
                    recommendation,
                )

                existing.updatedAt = now

                self.repository.update(
                    meeting_id,
                    existing,
                )

                return existing

            #
            # Normal OPEN -> UPDATE.
            #
            self._copy_generated_content(
                existing,
                recommendation,
            )

            existing.status = "open"
            existing.updatedAt = now

            self.repository.update(
                meeting_id,
                existing,
            )

            return existing

        #
        # Recommendation is no longer supported by an active Finding.
        #
        if existing.status != "obsolete":

            existing.status = "obsolete"
            existing.updatedAt = now

            self.repository.update(
                meeting_id,
                existing,
            )

        return existing

    def accept(
        self,
        meeting_id: str,
        recommendation_id: str,
    ) -> Optional[Recommendation]:

        recommendation = (
            self.repository.find_by_id(
                meeting_id,
                recommendation_id,
            )
        )

        if recommendation is None:
            return None

        if recommendation.status == "obsolete":
            return recommendation

        recommendation.status = "accepted"
        recommendation.updatedAt = datetime.now(
            timezone.utc
        )

        self.repository.update(
            meeting_id,
            recommendation,
        )

        return recommendation

    def complete(
        self,
        meeting_id: str,
        recommendation_id: str,
    ) -> Optional[Recommendation]:

        recommendation = (
            self.repository.find_by_id(
                meeting_id,
                recommendation_id,
            )
        )

        if recommendation is None:
            return None

        now = datetime.now(
            timezone.utc
        )

        recommendation.status = "completed"
        recommendation.completedAt = now
        recommendation.updatedAt = now

        self.repository.update(
            meeting_id,
            recommendation,
        )

        return recommendation

    def dismiss(
        self,
        meeting_id: str,
        recommendation_id: str,
    ) -> Optional[Recommendation]:

        recommendation = (
            self.repository.find_by_id(
                meeting_id,
                recommendation_id,
            )
        )

        if recommendation is None:
            return None

        now = datetime.now(
            timezone.utc
        )

        recommendation.status = "dismissed"
        recommendation.dismissedAt = now
        recommendation.updatedAt = now

        self.repository.update(
            meeting_id,
            recommendation,
        )

        return recommendation

    @staticmethod
    def _copy_generated_content(
        target: Recommendation,
        source: Recommendation,
    ) -> None:
        """
        Refresh generated content without changing lifecycle identity.

        Keep:
            id
            fingerprint
            firstObservedAt
            current user lifecycle status

        Refresh:
            Finding relation
            human-readable content
            evidence
            confidence
            machine-readable attributes
        """

        target.findingId = (
            source.findingId
        )

        target.type = (
            source.type
        )

        target.domain = (
            source.domain
        )

        target.subject = (
            source.subject
        )

        target.title = (
            source.title
        )

        target.summary = (
            source.summary
        )

        target.action = (
            source.action
        )

        target.priority = (
            source.priority
        )

        target.confidence = (
            source.confidence
        )

        target.sourceIds = list(
            source.sourceIds
        )

        target.evidence = list(
            source.evidence
        )

        target.attributes = dict(
            source.attributes
        )

        target.reasonCode = (
            source.reasonCode
        )


recommendation_lifecycle_manager = (
    RecommendationLifecycleManager(
        recommendation_repository
    )
)