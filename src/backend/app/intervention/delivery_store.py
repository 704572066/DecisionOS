from __future__ import annotations

from datetime import datetime, timezone

from app.intervention.delivery_models import InterventionDelivery


class InterventionDeliveryStore:
    """Process-local delivery history. Replaceable by a durable repository later."""

    def __init__(self) -> None:
        self._records: dict[str, InterventionDelivery] = {}
        self._by_intervention: dict[tuple[str, str], str] = {}

    def put(self, record: InterventionDelivery) -> InterventionDelivery:
        self._records[record.id] = record
        self._by_intervention[(record.meetingId, record.interventionId)] = record.id
        return record

    def for_intervention(self, meeting_id: str, intervention_id: str) -> InterventionDelivery | None:
        delivery_id = self._by_intervention.get((meeting_id, intervention_id))
        return self._records.get(delivery_id) if delivery_id else None

    def get(self, delivery_id: str) -> InterventionDelivery | None:
        return self._records.get(delivery_id)

    def list(self, meeting_id: str) -> list[InterventionDelivery]:
        self.expire(meeting_id)
        return sorted(
            (item for item in self._records.values() if item.meetingId == meeting_id),
            key=lambda item: item.createdAt,
            reverse=True,
        )

    def pending(self, meeting_id: str) -> list[InterventionDelivery]:
        return [item for item in self.list(meeting_id) if item.status == "pending"]

    def expire(self, meeting_id: str | None = None) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        for item in self._records.values():
            if meeting_id is not None and item.meetingId != meeting_id:
                continue
            if item.status in {"pending", "delivered"} and item.expiresAt <= now:
                item.status = "expired"
                item.expiredAt = now
                count += 1
        return count


intervention_delivery_store = InterventionDeliveryStore()

