from app.runtime.semantic_event_validator import semantic_event_validator
from app.runtime.semantic_models import SemanticEventCandidate


def candidate(**kwargs):
    defaults = dict(
        domain="delivery",
        kind="constraint",
        field="deadline",
        value="月底",
        normalizedValue="2026-08-31",
        sourceText="必须月底前上线",
        confidence=0.95,
    )
    defaults.update(kwargs)
    return SemanticEventCandidate(**defaults)


def test_validator_accepts_delivery_constraint():
    output = semantic_event_validator.validate(
        [candidate()],
        source_text="必须月底前上线",
    )
    assert len(output) == 1
    assert output[0].domain == "delivery"
    assert output[0].field == "deadline"


def test_validator_rejects_low_confidence():
    output = semantic_event_validator.validate(
        [candidate(confidence=0.3)],
        source_text="可能月底上线",
    )
    assert output == []


def test_validator_rejects_invalid_discount():
    output = semantic_event_validator.validate(
        [candidate(
            domain="commercial",
            kind="fact_change",
            field="discountPercent",
            normalizedValue=130,
            confidence=0.99,
        )],
        source_text="折扣130%",
    )
    assert output == []

from datetime import datetime


def test_validator_anchors_yearless_delivery_date_to_meeting_date():
    output = semantic_event_validator.validate(
        [candidate(
            field="goLiveDate",
            sourceText="10月1日上线时间可以接受",
            normalizedValue="2025-10-01",
        )],
        source_text="10月1日上线时间可以接受",
        meeting_date=datetime(2026, 8, 12, 10, 0, 0),
    )
    assert output[0].normalizedValue == "2026-10-01"


def test_validator_moves_contract_approval_dependency_to_approval_domain():
    output = semantic_event_validator.validate(
        [candidate(
            domain="contract",
            kind="dependency",
            field="signing",
            value="集团法务确认",
            normalizedValue=None,
            relation="conditional_on",
            target="合同签署",
            actor="集团法务",
            sourceText="最终合同还是需要集团法务确认以后才能签署",
        )],
        source_text="最终合同还是需要集团法务确认以后才能签署",
        meeting_date=datetime(2026, 8, 12),
    )
    assert output[0].domain == "approval"
    assert output[0].field == "contractApproval"
    assert output[0].actor == "third_party"
    assert output[0].metadata["actorText"] == "集团法务"


def test_validator_uses_unknown_actor_when_not_explicit():
    output = semantic_event_validator.validate(
        [candidate(actor="")],
        source_text="必须月底前上线",
        meeting_date=datetime(2026, 8, 12),
    )
    assert output[0].actor == "unknown"
