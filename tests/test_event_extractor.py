from app.runtime.event_extractor import event_extractor
from app.runtime.models import RuntimeState


def state(payment=180, discount=18):
    return RuntimeState(
        meetingId="m1",
        projectId="p1",
        contextId="c1",
        decisionFacts={
            "paymentTermDays": payment,
            "discountPercent": discount,
        },
    )


def test_payment_change_and_risk_resolution():
    events = event_extractor.extract(
        "m1",
        "客户同意把付款周期调整到90天。",
        state(),
    )
    types = [event.type for event in events]
    assert "PaymentTermChanged" in types
    assert "RiskResolved" in types
    payment = next(
        event for event in events
        if event.type == "PaymentTermChanged"
    )
    assert payment.previousValue == 180
    assert payment.value == 90


def test_discount_change():
    events = event_extractor.extract(
        "m1",
        "折扣可以调整到12%。",
        state(),
    )
    changed = [
        event for event in events
        if event.type == "PriceChanged"
    ]
    assert changed
    assert changed[0].value == 12
