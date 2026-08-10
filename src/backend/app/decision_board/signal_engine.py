from app.decision_board.signal import DecisionSignal


class DecisionSignalEngine:
    def build(self, events):
        result = []
        seen = set()

        for event in events or []:
            event_type = event.get("type")
            source_text = (
                event.get("sourceText")
                or "会议条件发生变化"
            )

            if event_type == "RiskResolved":
                signal = DecisionSignal(
                    level="NEXT",
                    type="risk_resolved",
                    title="付款风险下降",
                    message=source_text,
                )

            elif event_type == "PaymentTermChanged":
                signal = DecisionSignal(
                    level="NEXT",
                    type="runtime_change",
                    title="付款条件发生变化",
                    message=source_text,
                )

            elif event_type in [
                "DiscountChanged",
                "PriceChanged",
            ]:
                signal = DecisionSignal(
                    level="NOW",
                    type="risk_signal",
                    title="检测到价格风险",
                    message="价格条件发生变化，请重新确认利润影响",
                )

            else:
                continue

            key = (
                signal.level,
                signal.type,
                signal.message,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(signal)

        return result