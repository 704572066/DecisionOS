from app.decision_board.signal import DecisionSignal


class DecisionSignalEngine:
    def build(self, events):
        events = list(events or [])
        result = []

        latest_payment = None
        latest_price = None

        for event in events:
            event_type = event.get("type")

            if event_type == "PaymentTermChanged":
                latest_payment = event

            elif event_type in ["DiscountChanged", "PriceChanged"]:
                latest_price = event

        if latest_payment:
            signal = self._payment_signal(latest_payment)
            if signal:
                result.append(signal)

        if latest_price:
            signal = self._price_signal(latest_price)
            if signal:
                result.append(signal)

        return result

    @staticmethod
    def _payment_signal(event):
        previous = event.get("previousValue")
        value = event.get("value")

        if previous is not None and value is not None:
            previous = int(previous)
            value = int(value)

            if value > previous:
                return DecisionSignal(
                    level="NOW",
                    type="risk_signal",
                    title="付款条件恶化",
                    message=(
                        f"付款周期从{previous}天延长到{value}天，"
                        "请重新评估回款和现金流风险"
                    ),
                )

            if value < previous:
                return DecisionSignal(
                    level="NEXT",
                    type="risk_resolved",
                    title="付款风险下降",
                    message=(
                        f"付款周期从{previous}天调整到{value}天"
                    ),
                )

        return DecisionSignal(
            level="NEXT",
            type="runtime_change",
            title="付款条件发生变化",
            message=event.get("sourceText")
            or "付款条件发生变化",
        )

    @staticmethod
    def _price_signal(event):
        previous = event.get("previousValue")
        value = event.get("value")

        if previous is not None and value is not None:
            previous = float(previous)
            value = float(value)

            if value > previous:
                return DecisionSignal(
                    level="NOW",
                    type="risk_signal",
                    title="折扣风险上升",
                    message=(
                        f"折扣从{previous:g}%提高到{value:g}%，"
                        "请重新确认利润率影响"
                    ),
                )

            if value < previous:
                return DecisionSignal(
                    level="NEXT",
                    type="risk_resolved",
                    title="价格风险下降",
                    message=(
                        f"折扣从{previous:g}%降低到{value:g}%"
                    ),
                )

        return DecisionSignal(
            level="NOW",
            type="runtime_change",
            title="价格条件发生变化",
            message=event.get("sourceText")
            or "价格条件发生变化，请重新确认利润影响",
        )