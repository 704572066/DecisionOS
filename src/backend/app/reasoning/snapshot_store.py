from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from app.reasoning.models import ReasoningResult
from app.runtime.models import RuntimeState


@dataclass(frozen=True)
class ReasoningSnapshot:
    meetingId: str
    stateKey: str
    result: ReasoningResult
    createdAt: datetime


class ReasoningSnapshotStore:
    """Meeting-scoped shared ReasoningResult snapshots.

    DecisionBoard, Dialogue, and later interaction surfaces must consume
    the same ReasoningResult for the same RuntimeState instead of
    independently executing lifecycle-aware reasoning.
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, ReasoningSnapshot] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def state_key(state: RuntimeState) -> str:
        # contextId changes on a full runtime refresh; updatedAt and the
        # processed transcript sequence distinguish incremental revisions.
        updated_at = state.updatedAt.isoformat()
        return ":".join(
            [
                state.contextId or "_",
                str(state.lastProcessedSegmentSequence),
                updated_at,
            ]
        )

    def get(self, state: RuntimeState) -> ReasoningResult | None:
        snapshot = self._snapshots.get(state.meetingId)
        if snapshot is None:
            return None
        if snapshot.stateKey != self.state_key(state):
            return None
        return snapshot.result

    def put(
        self,
        state: RuntimeState,
        result: ReasoningResult,
    ) -> ReasoningResult:
        self._snapshots[state.meetingId] = ReasoningSnapshot(
            meetingId=state.meetingId,
            stateKey=self.state_key(state),
            result=result,
            createdAt=datetime.now(timezone.utc),
        )
        return result

    def clear(self, meeting_id: str) -> None:
        self._snapshots.pop(meeting_id, None)

    def lock(self, meeting_id: str) -> asyncio.Lock:
        lock = self._locks.get(meeting_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[meeting_id] = lock
        return lock


reasoning_snapshot_store = ReasoningSnapshotStore()
