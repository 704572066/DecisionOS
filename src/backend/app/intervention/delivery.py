from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from app.intervention.delivery_models import InterventionDelivery
from app.intervention.delivery_store import InterventionDeliveryStore, intervention_delivery_store
from app.intervention.models import InterventionDecision

logger = logging.getLogger(__name__)


class MeetingConnectionHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, meeting_id: str, websocket: Any) -> None:
        async with self._lock:
            self._connections.setdefault(meeting_id, set()).add(websocket)

    async def disconnect(self, meeting_id: str, websocket: Any) -> None:
        async with self._lock:
            sockets = self._connections.get(meeting_id)
            if sockets is None:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(meeting_id, None)

    async def send(self, meeting_id: str, payload: dict) -> int:
        async with self._lock:
            sockets = list(self._connections.get(meeting_id, set()))
        delivered = 0
        stale: list[Any] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
                delivered += 1
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            await self.disconnect(meeting_id, websocket)
        return delivered

    def connection_count(self, meeting_id: str) -> int:
        return len(self._connections.get(meeting_id, set()))


class ActiveInterventionDeliveryService:
    def __init__(self, *, store: InterventionDeliveryStore | None = None, ttl_seconds: int = 300) -> None:
        self.store = store or intervention_delivery_store
        self.ttl_seconds = ttl_seconds
        self.hub = MeetingConnectionHub()

    async def deliver(self, decisions: list[InterventionDecision]) -> dict:
        diagnostics = {
            "eligibleCount": 0,
            "createdCount": 0,
            "pendingCount": 0,
            "deliveredCount": 0,
            "duplicateCount": 0,
            "failedCount": 0,
        }
        for decision in decisions:
            if decision.level != "interrupt":
                continue
            diagnostics["eligibleCount"] += 1
            existing = self.store.for_intervention(decision.meetingId, decision.id)
            if existing is not None:
                diagnostics["duplicateCount"] += 1
                continue
            record = self._create(decision)
            self.store.put(record)
            diagnostics["createdCount"] += 1
            try:
                if await self._send(record):
                    diagnostics["deliveredCount"] += 1
                else:
                    diagnostics["pendingCount"] += 1
            except Exception as exc:
                record.lastError = str(exc)
                diagnostics["failedCount"] += 1
                diagnostics["pendingCount"] += 1
                logger.exception("Active intervention delivery failed: meeting=%s", decision.meetingId)
        return diagnostics

    async def connection_opened(self, meeting_id: str, websocket: Any) -> dict:
        await self.hub.connect(meeting_id, websocket)
        delivered = 0
        for record in self.store.pending(meeting_id):
            if await self._send(record):
                delivered += 1
        return {"pendingDeliveredCount": delivered}

    async def connection_closed(self, meeting_id: str, websocket: Any) -> None:
        await self.hub.disconnect(meeting_id, websocket)

    def acknowledge(self, meeting_id: str, delivery_id: str) -> InterventionDelivery | None:
        self.store.expire(meeting_id)
        record = self.store.get(delivery_id)
        if record is None or record.meetingId != meeting_id or record.status == "expired":
            return None
        if record.status != "acknowledged":
            record.status = "acknowledged"
            record.acknowledgedAt = datetime.now(timezone.utc)
        return record

    def diagnostics(self, meeting_id: str) -> dict:
        records = self.store.list(meeting_id)
        return {
            "meetingId": meeting_id,
            "connectionCount": self.hub.connection_count(meeting_id),
            "deliveryCount": len(records),
            "pendingCount": sum(x.status == "pending" for x in records),
            "deliveredCount": sum(x.status == "delivered" for x in records),
            "acknowledgedCount": sum(x.status == "acknowledged" for x in records),
            "expiredCount": sum(x.status == "expired" for x in records),
        }

    def _create(self, decision: InterventionDecision) -> InterventionDelivery:
        now = datetime.now(timezone.utc)
        digest = sha256(f"{decision.meetingId}:{decision.id}".encode()).hexdigest()[:16]
        return InterventionDelivery(
            id=f"delivery-{digest}",
            meetingId=decision.meetingId,
            interventionId=decision.id,
            fingerprint=decision.fingerprint,
            expiresAt=now + timedelta(seconds=self.ttl_seconds),
            event={
                "type": "intervention.delivered",
                "deliveryId": f"delivery-{digest}",
                "intervention": decision.model_dump(mode="json"),
            },
        )

    async def _send(self, record: InterventionDelivery) -> bool:
        record.attemptCount += 1
        recipient_count = await self.hub.send(record.meetingId, record.event)
        if recipient_count == 0:
            return False
        record.status = "delivered"
        record.deliveredAt = datetime.now(timezone.utc)
        record.lastError = ""
        return True


active_intervention_delivery = ActiveInterventionDeliveryService()
