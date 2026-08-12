import asyncio

from app.runtime.hybrid_event_extractor import HybridEventExtractor
from app.runtime.models import RuntimeState
from app.runtime.semantic_models import SemanticEventCandidate


def state():
    return RuntimeState(
        meetingId="m1",
        projectId="p1",
        contextId="c1",
        decisionFacts={"discountPercent": 18},
    )


def test_semantic_extractor_supplements_new_domain(monkeypatch):
    extractor = HybridEventExtractor()

    async def fake_extract(text, previous):
        return [SemanticEventCandidate(
            domain="approval",
            kind="dependency",
            field="finalContractApproval",
            value="集团法务确认",
            relation="requires",
            sourceText="最终合同还是需要集团法务确认",
            confidence=0.98,
        )]

    monkeypatch.setattr(
        "app.runtime.hybrid_event_extractor.semantic_event_extractor.extract",
        fake_extract,
    )

    events = asyncio.run(extractor.extract(
        "m1",
        "最终合同还是需要集团法务确认",
        state(),
    ))
    assert len(events) == 1
    assert events[0].type == "SemanticObjectRecorded"
    assert events[0].metadata["domain"] == "approval"


def test_rule_price_event_remains_authoritative(monkeypatch):
    extractor = HybridEventExtractor()

    async def fake_extract(text, previous):
        return [SemanticEventCandidate(
            domain="commercial",
            kind="fact_change",
            field="discountPercent",
            normalizedValue=8,
            sourceText=text,
            confidence=0.99,
        )]

    monkeypatch.setattr(
        "app.runtime.hybrid_event_extractor.semantic_event_extractor.extract",
        fake_extract,
    )

    events = asyncio.run(extractor.extract(
        "m1",
        "客户要求整体价格下降8%",
        state(),
    ))
    price_events = [event for event in events if event.type == "PriceChanged"]
    semantic_price = [
        event for event in events
        if event.type == "SemanticObjectRecorded"
        and event.field == "discountPercent"
    ]
    assert len(price_events) == 1
    assert price_events[0].value == 8
    assert semantic_price == []
