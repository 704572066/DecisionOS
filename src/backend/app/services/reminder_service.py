from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock

from sqlalchemy.orm import Session

from app.core.config import settings
from app.intelligence.reminder_engine import ai_reminder_engine
from app.models.entities import Meeting
from app.observability.runtime_metrics import runtime_metrics


@dataclass
class ReminderState:
    last_analyzed_length: int = 0
    last_analyzed_at: float = 0.0
    last_accessed_at: float = field(default_factory=time.monotonic)
    sent_keys: set[str] = field(default_factory=set)


class RealtimeReminderCoordinator:
    def __init__(self) -> None:
        self._states: dict[str, ReminderState] = {}
        self._lock = RLock()

    async def analyze_if_due(
        self,
        db: Session,
        meeting: Meeting,
        *,
        force: bool = False,
    ) -> dict | None:
        now = time.monotonic()

        with self._lock:
            state = self._states.setdefault(meeting.id, ReminderState())
            state.last_accessed_at = now
            transcript = meeting.transcript or ""
            new_chars = max(0, len(transcript) - state.last_analyzed_length)
            cooldown_elapsed = (
                now - state.last_analyzed_at
                >= settings.reminder_cooldown_seconds
            )

            if not force and (
                new_chars < settings.reminder_min_chars
                or not cooldown_elapsed
            ):
                return None

            # Reserve the current transcript length before network I/O to avoid
            # duplicate concurrent LLM calls for the same meeting.
            state.last_analyzed_length = len(transcript)
            state.last_analyzed_at = now

        analysis_started = time.perf_counter()
        result = await ai_reminder_engine.generate(db, meeting)
        runtime_metrics.record_reminder_duration(
            (time.perf_counter() - analysis_started) * 1000
        )

        deduplicated = []
        with self._lock:
            state = self._states.setdefault(meeting.id, ReminderState())
            for reminder in result.get("reminders", []):
                source_ids = ",".join(
                    sorted(
                        str(source.get("id"))
                        for source in reminder.get("sources", [])
                        if source.get("id")
                    )
                )
                key = (
                    f"{reminder.get('type')}:{reminder.get('title')}:"
                    f"{source_ids}"
                )
                if key in state.sent_keys:
                    continue
                state.sent_keys.add(key)
                deduplicated.append(reminder)

            self._remove_stale_states(time.monotonic())

        return {
            **result,
            "reminders": deduplicated,
        }

    def cleanup(self, meeting_id: str) -> None:
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
