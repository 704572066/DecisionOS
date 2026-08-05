from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Meeting
from app.services.context_service import analyze_meeting


@dataclass
class ReminderState:
    last_analyzed_length: int = 0
    last_analyzed_at: float = 0.0
    last_accessed_at: float = field(default_factory=time.monotonic)
    sent_keys: set[str] = field(default_factory=set)


class RealtimeReminderCoordinator:
    """In-process reminder throttle for the Demo.

    State is intentionally session-scoped and non-durable. A later Sprint can
    persist reminder delivery records in PostgreSQL.
    """

    def __init__(self) -> None:
        self._states: dict[str, ReminderState] = {}
        self._lock = RLock()

    def analyze_if_due(
        self,
        db: Session,
        meeting: Meeting,
        *,
        force: bool = False,
    ) -> dict | None:
        with self._lock:
            state = self._states.setdefault(meeting.id, ReminderState())
            state.last_accessed_at = time.monotonic()

            transcript = meeting.transcript or ""
            new_chars = max(0, len(transcript) - state.last_analyzed_length)
            now = time.monotonic()
            cooldown_elapsed = (
                now - state.last_analyzed_at
                >= settings.reminder_cooldown_seconds
            )

            if not force and (
                new_chars < settings.reminder_min_chars or not cooldown_elapsed
            ):
                return None

            result = analyze_meeting(db, meeting)
            deduplicated = []
            for reminder in result.get("reminders", []):
                source = reminder.get("source") or {}
                key = (
                    f"{source.get('type')}:{source.get('id')}:"
                    f"{reminder.get('title')}:{reminder.get('summary')}"
                )
                if key in state.sent_keys:
                    continue
                state.sent_keys.add(key)
                deduplicated.append(reminder)

            state.last_analyzed_length = len(transcript)
            state.last_analyzed_at = now

            self._remove_stale_states(now)
            return {
                "meetingId": meeting.id,
                "topics": result.get("topics", []),
                "reminders": deduplicated,
            }

    def cleanup(self, meeting_id: str) -> None:
        """Remove volatile state when a meeting is explicitly completed."""
        with self._lock:
            self._states.pop(meeting_id, None)

    def _remove_stale_states(self, now: float) -> None:
        max_idle_seconds = 6 * 60 * 60
        stale_ids = [
            meeting_id
            for meeting_id, state in self._states.items()
            if now - state.last_accessed_at > max_idle_seconds
        ]
        for meeting_id in stale_ids:
            self._states.pop(meeting_id, None)


realtime_reminder_coordinator = RealtimeReminderCoordinator()
