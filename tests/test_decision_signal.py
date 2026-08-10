from src.backend.app.decision_board.signal_engine import DecisionSignalEngine

def test_signal():
    result = DecisionSignalEngine().build([{"type":"PaymentTermChanged"}])
    assert result[0].level == "NEXT"
