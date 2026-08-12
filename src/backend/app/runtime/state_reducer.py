from __future__ import annotations

from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState


class RuntimeStateReducer:
    @staticmethod
    def _clear_stale_accepted_condition(
        facts: dict,
        event: DecisionEvent,
        previous_value,
        new_value,
    ) -> None:
        last_accepted = facts.get("lastAcceptedCondition")

        if (
            last_accepted
            and previous_value is not None
            and new_value != previous_value
            and str(event.sourceText).strip() != str(last_accepted).strip()
        ):
            facts.pop("lastAcceptedCondition", None)

    def apply(
        self,
        state: RuntimeState,
        events: list[DecisionEvent],
    ) -> RuntimeState:
        facts = dict(state.decisionFacts)
        resolved = list(state.resolvedRiskKeys)
        recent = list(state.recentEvents)

        for event in events:
            if event.type == "PriceChanged" and event.value is not None:
                new_value = float(event.value)
                previous_value = (
                    float(event.previousValue)
                    if event.previousValue is not None
                    else facts.get("discountPercent")
                )

                facts["discountPercent"] = new_value

                self._clear_stale_accepted_condition(
                    facts,
                    event,
                    previous_value,
                    new_value,
                )

                # Sprint 3-3: discount risk lifecycle
                discount_risk_key = "discount"

                # 折扣重新进入风险区：重新打开风险
                if new_value > 10:
                    if discount_risk_key in resolved:
                        resolved.remove(discount_risk_key)

                # 折扣进入安全区：标记风险解除
                elif new_value <= 10:
                    if discount_risk_key not in resolved:
                        resolved.append(discount_risk_key)

            elif event.type == "PaymentTermChanged" and event.value is not None:
                new_value = int(event.value)
                previous_value = (
                    int(event.previousValue)
                    if event.previousValue is not None
                    else facts.get("paymentTermDays")
                )

                facts["paymentTermDays"] = new_value

                self._clear_stale_accepted_condition(
                    facts,
                    event,
                    previous_value,
                    new_value,
                )

                # If payment terms worsen after being resolved, re-open the
                # payment risk instead of leaving stale resolved state behind.
                payment_risk_key = "payment_term"
                if (
                    previous_value is not None
                    and new_value > 120
                    and payment_risk_key in resolved
                ):
                    # resolved.remove("payment_term")
                    resolved.remove(payment_risk_key)
                elif (
                    previous_value is not None
                    and new_value <= 120
                    and payment_risk_key not in resolved
                ):
                    # resolved.remove("payment_term")
                    resolved.append(payment_risk_key)

            elif event.type == "ConstraintAdded":
                constraints = list(facts.get("runtimeConstraints") or [])
                text = str(event.value or event.sourceText)
                if text and text not in constraints:
                    constraints.append(text)
                facts["runtimeConstraints"] = constraints[-10:]

            elif event.type == "ConditionAccepted":
                facts["lastAcceptedCondition"] = str(
                    event.value or event.sourceText
                )

            elif event.type == "ConditionRejected":
                facts["lastRejectedCondition"] = str(
                    event.value or event.sourceText
                )

            elif event.type == "RiskResolved":
                key = None
                if event.field == "paymentTermDays":
                    key = "payment_term"
                elif event.field == "discountPercent":
                    key = "discount"
                else:
                    key = None
                if key and key not in resolved:
                    resolved.append(key)

            recent.append(event.model_dump(mode="json"))

        state.decisionFacts = facts
        state.resolvedRiskKeys = resolved[-20:]
        state.recentEvents = recent[-20:]
        return state


runtime_state_reducer = RuntimeStateReducer()
