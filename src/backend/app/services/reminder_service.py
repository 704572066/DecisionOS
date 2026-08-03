from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Meeting
from app.services.context_service import analyze_meeting


@dataclass
class ReminderState:
    last_analyzed_length: int = 0
    last_analyzed_at: float = 0.0
    sent_keys: set[str] = field(default_factory=set)


class RealtimeReminderCoordinator:
    def __init__(self) -> None:
        self._states: dict[str, ReminderState] = {}

    def analyze_if_due(self, db: Session, meeting: Meeting, *, force: bool = False) -> dict | None:
        state = self._states.setdefault(meeting.id, ReminderState())
        transcript = meeting.transcript or ""
        new_chars = len(transcript) - state.last_analyzed_length
        now = time.monotonic()
        cooldown_elapsed = now - state.last_analyzed_at >= settings.reminder_cooldown_seconds

        if not force and (new_chars < settings.reminder_min_chars or not cooldown_elapsed):
            return None

        result = analyze_meeting(db, meeting)
        deduplicated = []
        for reminder in result.get("reminders", []):
            source = reminder.get("source") or {}
            key = f"{source.get('type')}:{source.get('id')}:{reminder.get('title')}"
            if key in state.sent_keys:
                continue
            state.sent_keys.add(key)
            deduplicated.append(reminder)

        state.last_analyzed_length = len(transcript)
        state.last_analyzed_at = now
        return {
            "meetingId": meeting.id,
            "topics": result.get("topics", []),
            "reminders": deduplicated,
        }


realtime_reminder_coordinator = RealtimeReminderCoordinator()
