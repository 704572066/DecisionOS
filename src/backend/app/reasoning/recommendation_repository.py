from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.reasoning.recommendation_models import (
    Recommendation,
)


class RecommendationRepository:
    """
    Meeting-scoped in-memory Recommendation repository.

    Identity:

        (meetingId, fingerprint)

    The fingerprint, rather than Recommendation id or generated text,
    is used as lifecycle identity.
    """

    def __init__(self) -> None:
        self._recommendations: Dict[
            Tuple[str, str],
            Recommendation,
        ] = {}

    @staticmethod
    def _key(
        meeting_id: str,
        fingerprint: str,
    ) -> Tuple[str, str]:
        return (
            meeting_id,
            fingerprint,
        )

    def save(
        self,
        meeting_id: str,
        recommendation: Recommendation,
    ) -> Recommendation:

        self._recommendations[
            self._key(
                meeting_id,
                recommendation.fingerprint,
            )
        ] = recommendation

        return recommendation

    def update(
        self,
        meeting_id: str,
        recommendation: Recommendation,
    ) -> Recommendation:

        self._recommendations[
            self._key(
                meeting_id,
                recommendation.fingerprint,
            )
        ] = recommendation

        return recommendation

    def find_by_fingerprint(
        self,
        meeting_id: str,
        fingerprint: str,
    ) -> Optional[Recommendation]:

        return self._recommendations.get(
            self._key(
                meeting_id,
                fingerprint,
            )
        )

    def find_by_id(
        self,
        meeting_id: str,
        recommendation_id: str,
    ) -> Optional[Recommendation]:

        for (
            stored_meeting_id,
            _,
        ), recommendation in self._recommendations.items():

            if stored_meeting_id != meeting_id:
                continue

            if recommendation.id == recommendation_id:
                return recommendation

        return None

    def list(
        self,
        meeting_id: Optional[str] = None,
    ) -> List[Recommendation]:

        if meeting_id is None:
            return list(
                self._recommendations.values()
            )

        return [
            recommendation
            for (
                stored_meeting_id,
                _,
            ), recommendation
            in self._recommendations.items()
            if stored_meeting_id == meeting_id
        ]


recommendation_repository = (
    RecommendationRepository()
)