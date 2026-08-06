from __future__ import annotations

import os
import threading
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class RecentError:
    timestamp: str
    category: str
    message: str
    request_id: str = ""
    meeting_id: str = ""


class RuntimeMetrics:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._lock = threading.RLock()
        self._active_websockets: set[str] = set()
        self._requests_total = 0
        self._requests_in_flight = 0
        self._http_errors_total = 0
        self._unhandled_errors_total = 0
        self._request_duration_ms_total = 0.0
        self._status_codes: Counter[int] = Counter()
        self._recent_errors: deque[RecentError] = deque(maxlen=20)
        self._last_reminder_duration_ms: float | None = None
        self._last_reminder_at: str | None = None

    def request_started(self) -> None:
        with self._lock:
            self._requests_total += 1
            self._requests_in_flight += 1

    def request_finished(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._requests_in_flight = max(0, self._requests_in_flight - 1)
            self._status_codes[status_code] += 1
            self._request_duration_ms_total += duration_ms
            if status_code >= 400:
                self._http_errors_total += 1

    def request_failed(self) -> None:
        with self._lock:
            self._requests_in_flight = max(0, self._requests_in_flight - 1)
            self._unhandled_errors_total += 1

    def websocket_opened(self, meeting_id: str) -> None:
        with self._lock:
            self._active_websockets.add(meeting_id)

    def websocket_closed(self, meeting_id: str) -> None:
        with self._lock:
            self._active_websockets.discard(meeting_id)

    def record_error(
        self,
        *,
        category: str,
        message: str,
        request_id: str = "",
        meeting_id: str = "",
    ) -> None:
        with self._lock:
            self._recent_errors.appendleft(
                RecentError(
                    timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    category=category,
                    message=message[:500],
                    request_id=request_id,
                    meeting_id=meeting_id,
                )
            )

    def record_reminder_duration(self, duration_ms: float) -> None:
        with self._lock:
            self._last_reminder_duration_ms = round(duration_ms, 2)
            self._last_reminder_at = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )

    def snapshot(self) -> dict:
        with self._lock:
            average_ms = (
                self._request_duration_ms_total / self._requests_total
                if self._requests_total
                else 0.0
            )
            return {
                "processId": os.getpid(),
                "uptimeSeconds": int(time.time() - self.started_at),
                "requestsTotal": self._requests_total,
                "requestsInFlight": self._requests_in_flight,
                "httpErrorsTotal": self._http_errors_total,
                "unhandledErrorsTotal": self._unhandled_errors_total,
                "averageRequestDurationMs": round(average_ms, 2),
                "statusCodes": dict(self._status_codes),
                "activeWebSocketCount": len(self._active_websockets),
                "activeMeetingIds": sorted(self._active_websockets),
                "lastReminderDurationMs": self._last_reminder_duration_ms,
                "lastReminderAt": self._last_reminder_at,
                "recentErrors": [asdict(item) for item in self._recent_errors],
            }


runtime_metrics = RuntimeMetrics()
