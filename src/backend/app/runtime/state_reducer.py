from __future__ import annotations

from typing import Any

from app.runtime.decision_state import decision_state_resolver
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

    @staticmethod
    def _apply_semantic_object(
        facts: dict,
        event: DecisionEvent,
    ) -> None:
        metadata = dict(event.metadata or {})
        domain = str(metadata.get("domain") or "other")
        kind = str(metadata.get("kind") or "unknown")

        item = {
            "domain": domain,
            "kind": kind,
            "field": event.field,
            "value": event.value,
            "relation": metadata.get("relation") or "",
            "role": metadata.get("role") or "unknown",
            "actor": metadata.get("actor") or "unknown",
            "target": metadata.get("target") or "",
            "status": metadata.get("status") or "",
            "confidence": metadata.get("confidence"),
            "sourceText": event.sourceText,
            "eventId": event.eventId,
        }

        history = list(facts.get("semanticHistory") or [])

        if not any(
            current.get("eventId") == event.eventId
            for current in history
        ):
            history.append(item)

        facts["semanticHistory"] = history[-100:]

        semantic_state = dict(
            facts.get("semanticState") or {}
        )

        domain_items = list(
            semantic_state.get(domain) or []
        )

        slot = (
            kind,
            event.field or "",
            item["target"],
            item["actor"],
            item["role"],
        )

        def same_slot(current: dict) -> bool:
            return (
                current.get("kind") == slot[0]
                and (current.get("field") or "") == slot[1]
                and (current.get("target") or "") == slot[2]
                and (current.get("actor") or "unknown") == slot[3]
                and (current.get("role") or "unknown") == slot[4]
            )

        if item["status"] in {
            "withdrawn",
            "rejected",
        }:
            domain_items = [
                current
                for current in domain_items
                if not same_slot(current)
            ]

        else:
            replaced = False

            if event.field or item["target"]:
                for index, current in enumerate(
                    domain_items
                ):
                    if same_slot(current):
                        domain_items[index] = item
                        replaced = True
                        break

            if not replaced:
                duplicate = any(
                    current.get("kind") == item["kind"]
                    and current.get("field") == item["field"]
                    and current.get("value") == item["value"]
                    and current.get("relation") == item["relation"]
                    and current.get("actor") == item["actor"]
                    and current.get("target") == item["target"]
                    and (
                        current.get("role")
                        or "unknown"
                    ) == item["role"]
                    for current in domain_items
                )

                if not duplicate:
                    domain_items.append(item)

        if domain_items:
            semantic_state[domain] = (
                domain_items[-20:]
            )
        else:
            semantic_state.pop(
                domain,
                None,
            )

        facts["semanticState"] = semantic_state

    @staticmethod
    def _flatten_decision_state(
        decision_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        state = decision_state or {}
        output: dict[str, Any] = {}

        commercial = state.get("commercial") or {}

        if "discountPercent" in commercial:
            output[
                "commercial.discountPercent"
            ] = commercial.get(
                "discountPercent"
            )

        if "paymentTermDays" in commercial:
            output[
                "commercial.paymentTermDays"
            ] = commercial.get(
                "paymentTermDays"
            )

        delivery = state.get("delivery") or {}

        if "goLiveDate" in delivery:
            output[
                "delivery.goLiveDate"
            ] = delivery.get(
                "goLiveDate"
            )

        scope = state.get("scope") or {}

        if scope:
            output[
                "scope.current"
            ] = {
                "value": scope.get("value"),
                "relation": scope.get("relation"),
                "status": scope.get("status"),
            }

        resource = state.get("resource") or {}

        if "maxTeamSize" in resource:
            output[
                "resource.maxTeamSize"
            ] = resource.get(
                "maxTeamSize"
            )

        approval = state.get("approval") or {}

        for key, value in approval.items():
            output[
                f"approval.{key}"
            ] = value

        contract = state.get("contract") or {}

        for key, value in contract.items():
            output[
                f"contract.{key}"
            ] = value

        return output

    @classmethod
    def _build_semantic_revisions(
        cls,
        previous_state: dict[str, Any] | None,
        current_state: dict[str, Any] | None,
    ) -> list[dict]:
        previous = cls._flatten_decision_state(
            previous_state
        )

        current = cls._flatten_decision_state(
            current_state
        )

        revisions: list[dict] = []

        keys = set(previous) | set(current)

        for field in sorted(keys):
            old_value = previous.get(field)
            new_value = current.get(field)

            if old_value == new_value:
                continue

            revisions.append(
                {
                    "type": "SemanticRevision",
                    "field": field,
                    "previousValue": old_value,
                    "currentValue": new_value,
                }
            )

        return revisions

    def apply(
        self,
        state: RuntimeState,
        events: list[DecisionEvent],
    ) -> RuntimeState:
        facts = dict(state.decisionFacts)

        resolved = list(
            state.resolvedRiskKeys
        )

        recent = list(
            state.recentEvents
        )

        previous_decision_state = dict(
            state.decisionState or {}
        )

        for event in events:
            if (
                event.type == "PriceChanged"
                and event.value is not None
            ):
                new_value = float(
                    event.value
                )

                previous_value = (
                    float(event.previousValue)
                    if event.previousValue is not None
                    else facts.get(
                        "discountPercent"
                    )
                )

                facts[
                    "discountPercent"
                ] = new_value

                self._clear_stale_accepted_condition(
                    facts,
                    event,
                    previous_value,
                    new_value,
                )

                discount_risk_key = (
                    "discount"
                )

                if new_value > 10:
                    if (
                        discount_risk_key
                        in resolved
                    ):
                        resolved.remove(
                            discount_risk_key
                        )

                elif new_value <= 10:
                    if (
                        discount_risk_key
                        not in resolved
                    ):
                        resolved.append(
                            discount_risk_key
                        )

            elif (
                event.type
                == "PaymentTermChanged"
                and event.value is not None
            ):
                new_value = int(
                    event.value
                )

                previous_value = (
                    int(event.previousValue)
                    if event.previousValue is not None
                    else facts.get(
                        "paymentTermDays"
                    )
                )

                facts[
                    "paymentTermDays"
                ] = new_value

                self._clear_stale_accepted_condition(
                    facts,
                    event,
                    previous_value,
                    new_value,
                )

                payment_risk_key = (
                    "payment_term"
                )

                if (
                    previous_value is not None
                    and new_value > 120
                    and payment_risk_key
                    in resolved
                ):
                    resolved.remove(
                        payment_risk_key
                    )

                elif (
                    previous_value is not None
                    and new_value <= 120
                    and payment_risk_key
                    not in resolved
                ):
                    resolved.append(
                        payment_risk_key
                    )

            elif event.type == "ConstraintAdded":
                constraints = list(
                    facts.get(
                        "runtimeConstraints"
                    )
                    or []
                )

                text = str(
                    event.value
                    or event.sourceText
                )

                if (
                    text
                    and text
                    not in constraints
                ):
                    constraints.append(
                        text
                    )

                facts[
                    "runtimeConstraints"
                ] = constraints[-10:]

            elif event.type == "ConditionAccepted":
                facts[
                    "lastAcceptedCondition"
                ] = str(
                    event.value
                    or event.sourceText
                )

            elif event.type == "ConditionRejected":
                facts[
                    "lastRejectedCondition"
                ] = str(
                    event.value
                    or event.sourceText
                )

            elif event.type == "SemanticObjectRecorded":
                self._apply_semantic_object(
                    facts,
                    event,
                )

            elif event.type == "RiskResolved":
                key = None

                if event.field == "paymentTermDays":
                    key = "payment_term"

                elif event.field == "discountPercent":
                    key = "discount"

                if (
                    key
                    and key not in resolved
                ):
                    resolved.append(
                        key
                    )

            recent.append(
                event.model_dump(
                    mode="json"
                )
            )

        new_decision_state = (
            decision_state_resolver.resolve(
                facts.get(
                    "semanticState"
                )
                or {}
            )
        )

        revisions = (
            self._build_semantic_revisions(
                previous_decision_state,
                new_decision_state,
            )
        )

        for revision in revisions:
            recent.append(
                revision
            )

        state.decisionFacts = facts

        state.decisionState = (
            new_decision_state
        )

        state.resolvedRiskKeys = (
            resolved[-20:]
        )

        state.recentEvents = (
            recent[-20:]
        )

        return state


runtime_state_reducer = RuntimeStateReducer()