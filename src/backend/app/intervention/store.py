from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class InterventionRecord:
    lastLevel: str
    lastEvaluatedAt: datetime
    lastInterruptAt: datetime | None = None


class InterventionStore:
    """In-memory meeting/finding interruption history for cooldown control."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], InterventionRecord] = {}

    def get(self, meeting_id: str, fingerprint: str) -> InterventionRecord | None:
        return self._records.get((meeting_id, fingerprint))

    def put(
        self,
        *,
        meeting_id: str,
        fingerprint: str,
        level: str,
        evaluated_at: datetime,
    ) -> InterventionRecord:
        key = (meeting_id, fingerprint)
        previous = self._records.get(key)
        last_interrupt = (
            evaluated_at
            if level == "interrupt"
            else previous.lastInterruptAt if previous else None
        )
        record = InterventionRecord(
            lastLevel=level,
            lastEvaluatedAt=evaluated_at,
            lastInterruptAt=last_interrupt,
        )
        self._records[key] = record
        return record

    def clear(self, meeting_id: str | None = None) -> None:
        if meeting_id is None:
            self._records.clear()
            return
        keys = [key for key in self._records if key[0] == meeting_id]
        for key in keys:
            self._records.pop(key, None)


intervention_store = InterventionStore()
