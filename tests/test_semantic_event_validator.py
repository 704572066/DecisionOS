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
