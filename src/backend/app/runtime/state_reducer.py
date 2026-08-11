from __future__ import annotations

from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState


class RuntimeStateReducer:

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
                if event.field == "paymentTermDays":
                    key = "payment_term"
                    if key not in resolved:
                        resolved.append(key)

            recent.append(event.model_dump(mode="json"))

        state.decisionFacts = facts
        state.resolvedRiskKeys = resolved[-20:]
        state.recentEvents = recent[-20:]
        return state


runtime_state_reducer = RuntimeStateReducer()
