from app.runtime.decision_state import decision_state_resolver


def test_customer_requirement_does_not_become_effective_commercial_state():
    state = {
        "commercial": [
            {
                "field": "paymentTerms",
                "value": 120,
                "role": "requirement",
                "status": "proposed",
                "actor": "customer",
            }
        ]
    }
    assert decision_state_resolver.resolve(state).get("commercial") is None


def test_proposal_becomes_current_when_no_stronger_state_exists():
    state = {
        "commercial": [
            {
                "field": "paymentTerms",
                "value": 90,
                "role": "proposal",
                "status": "proposed",
                "actor": "us",
            }
        ]
    }
    assert decision_state_resolver.resolve(state)["commercial"]["paymentTermDays"] == 90


def test_confirmed_discount_wins_over_requirement():
    state = {
        "commercial": [
            {
                "field": "priceReduction",
                "value": 0.18,
                "role": "requirement",
                "status": "proposed",
                "actor": "customer",
            },
            {
                "field": "priceReduction",
                "value": 0.08,
                "role": "acceptance",
                "status": "confirmed",
                "actor": "customer",
            },
        ]
    }
    assert decision_state_resolver.resolve(state)["commercial"]["discountPercent"] == 8


def test_approval_dependency_is_kept_for_downstream_reasoning():
    state = {
        "approval": [
            {
                "field": "legalApproval",
                "value": "required",
                "role": "dependency",
                "status": "confirmed",
                "actor": "third_party",
                "target": "contract signing",
                "sourceText": "最终合同需要集团法务确认",
            }
        ]
    }
    resolved = decision_state_resolver.resolve(state)
    assert resolved["approval"]["legalApproval"]["required"] is True
