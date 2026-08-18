import asyncio
from datetime import datetime, timedelta, timezone

from app.intervention.delivery import ActiveInterventionDeliveryService
from app.intervention.delivery_store import InterventionDeliveryStore
from app.intervention.models import InterventionDecision


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


def decision(identifier: str = "intervention-1") -> InterventionDecision:
    return InterventionDecision(
        id=identifier,
        meetingId="meeting-1",
        contextId="context-1",
        findingId="finding-1",
        level="interrupt",
        reasonCode="critical_decision_imminent",
        title="利润率可能跌破底线",
        message="请在承诺折扣前确认毛利率。",
        severity="high",
        urgency="critical",
        confidence=0.95,
        decisionRelevance=0.95,
        actionability=0.9,
        fingerprint="margin-floor",
    )


async def run() -> None:
    store = InterventionDeliveryStore()
    service = ActiveInterventionDeliveryService(store=store, ttl_seconds=300)

    pending_result = await service.deliver([decision()])
    assert pending_result["pendingCount"] == 1
    record = store.list("meeting-1")[0]
    assert record.status == "pending"

    socket = FakeWebSocket()
    opened = await service.connection_opened("meeting-1", socket)
    assert opened["pendingDeliveredCount"] == 1
    assert record.status == "delivered"
    assert socket.messages[0]["type"] == "intervention.delivered"

    acknowledged = service.acknowledge("meeting-1", record.id)
    assert acknowledged is not None
    assert acknowledged.status == "acknowledged"

    duplicate = await service.deliver([decision()])
    assert duplicate["duplicateCount"] == 1
    assert len(store.list("meeting-1")) == 1

    expired_store = InterventionDeliveryStore()
    expired_service = ActiveInterventionDeliveryService(store=expired_store)
    await expired_service.deliver([decision("intervention-expired")])
    expired = expired_store.list("meeting-1")[0]
    expired.expiresAt = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert expired_service.diagnostics("meeting-1")["expiredCount"] == 1
    assert expired.status == "expired"

    surface = decision("intervention-surface").model_copy(update={"level": "surface"})
    ignored = await service.deliver([surface])
    assert ignored["eligibleCount"] == 0

    await service.connection_closed("meeting-1", socket)
    print("PHASE 2.3.2 ACTIVE INTERVENTION DELIVERY: OK")


if __name__ == "__main__":
    asyncio.run(run())
