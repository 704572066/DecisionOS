from app.decision_board.signal import DecisionSignal


class DecisionSignalEngine:
    def build(self, events):
        result = []
        for event in events or []:
            event_type = event.get("type")
            if event_type in ["PaymentTermChanged", "ConditionAccepted"]:
                result.append(DecisionSignal(
                    level="NEXT",
                    type="runtime_change",
                    title="检测到条件变化",
                    message=event.get("sourceText") or "会议条件发生变化"
                ))
            elif event_type in ["DiscountChanged", "PriceChanged"]:
                result.append(DecisionSignal(
                    level="NOW",
                    type="risk_signal",
                    title="检测到价格风险",
                    message="价格条件发生变化，请重新确认利润影响"
                ))
        return result
