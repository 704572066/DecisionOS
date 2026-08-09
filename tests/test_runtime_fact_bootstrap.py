from app.runtime.service import RuntimeStateService

def test_bootstrap_discount_and_payment_days():
    context = {
        "cleanTranscriptWindow": "客户要求整体价格下降18%，并希望付款周期延长到180天。",
        "facts": [
            {"text": "18%", "factType": "percentage", "normalizedValue": "18%"},
            {"text": "180天", "factType": "duration", "normalizedValue": "180天"},
        ],
    }
    facts = RuntimeStateService._decision_facts_from_context(context)
    assert facts["discountPercent"] == 18.0
    assert facts["paymentTermDays"] == 180

def test_bootstrap_does_not_misclassify_unrelated_duration():
    context = {
        "cleanTranscriptWindow": "项目交付周期180天。",
        "facts": [
            {"text": "180天", "factType": "duration", "normalizedValue": "180天"}
        ],
    }
    facts = RuntimeStateService._decision_facts_from_context(context)
    assert "paymentTermDays" not in facts
