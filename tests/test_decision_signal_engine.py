from src.backend.app.decision_board.signal_engine import DecisionSignalEngine


def test_price_signal():
    result = DecisionSignalEngine().build([
        {"type": "PriceChanged", "value": 18}
    ])

    assert result[0].level == "NOW"


def test_payment_signal():
    result = DecisionSignalEngine().build([
        {"type": "PaymentTermChanged", "value": 90}
    ])

    assert result[0].type == "risk_resolved"
