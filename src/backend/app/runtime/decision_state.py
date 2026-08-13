from __future__ import annotations

from typing import Any


class DecisionStateResolver:
    """Resolve semantic positions into the current effective decision state.

    semanticState preserves the latest semantic position per party/slot.

    decisionState keeps only conditions that are useful as the current
    effective decision surface for downstream reasoning.

    Sprint 3-3.3.3:
    - requirement / assessment / unknown do not become effective decisions.
    - acceptance / commitment have highest semantic priority.
    - proposal can be used as a working condition when no stronger
      acceptance / commitment exists.
    - approval / contract dependencies remain available for downstream
      reasoning and are not treated as commercial decisions.
    """

    ROLE_PRIORITY = {
        "acceptance": 60,
        "commitment": 55,
        "proposal": 40,
        "dependency": 35,
        "requirement": 20,
        "assessment": 10,
        "liability": 10,
        "unknown": 0,
        "": 0,
    }

    STATUS_PRIORITY = {
        "confirmed":100,
        "accepted":90,
        "active":80,
        "pending":40,
        "proposed":20,
        "withdrawn":-100,
        "rejected":-100,
    }

    # Roles that may represent a current commercial/delivery working state.
    DECISION_ROLES = {
        "acceptance",
        "commitment",
        "proposal",
    }

    def resolve(
        self,
        semantic_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        state = semantic_state or {}
        result: dict[str, Any] = {}

        self._resolve_commercial(
            result,
            list(state.get("commercial") or []),
        )

        self._resolve_delivery(
            result,
            list(state.get("delivery") or []),
        )

        self._resolve_scope(
            result,
            list(state.get("scope") or []),
        )

        self._resolve_resource(
            result,
            list(state.get("resource") or []),
        )

        self._resolve_approval(
            result,
            list(state.get("approval") or []),
        )

        self._resolve_contract(
            result,
            list(state.get("contract") or []),
        )

        self._resolve_decision(
            result,
            list(state.get("decision") or []),
        )

        return result

    def _resolve_commercial(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        commercial: dict[str, Any] = {}

        discount = self._best_current(
            items,
            fields={
                "discountPercent",
                "priceReduction",
            },
        )

        if discount:
            value = self._number(
                discount.get("value")
            )

            if value is not None:
                if (
                    discount.get("field") == "priceReduction"
                    and 0 <= value <= 1
                ):
                    value *= 100

                commercial["discountPercent"] = value

        payment = self._best_current(
            items,
            fields={
                "paymentTermDays",
                "paymentTerms",
            },
        )

        if payment:
            value = self._number(
                payment.get("value")
            )

            if value is not None:
                commercial["paymentTermDays"] = int(value)

        if commercial:
            result["commercial"] = commercial

    def _resolve_delivery(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        selected = self._best_current(
            items,
            fields={
                "goLiveDate",
                "deliveryDate",
                "deadline",
            },
        )

        if selected:
            result["delivery"] = {
                "goLiveDate": selected.get("value"),
                "relation": selected.get("relation") or "",
                "role": selected.get("role") or "unknown",
                "status": selected.get("status") or "",
                "sourceText": selected.get("sourceText") or "",
            }

    def _resolve_scope(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        current = self._latest_effective_by_field(
            items,
            "scopeInclusion",
        )

        if not current:
            return

        result["scope"] = {
            "field": current.get("field") or "scopeInclusion",
            "value": current.get("value"),
            "relation": current.get("relation") or "",
            "role": current.get("role") or "unknown",
            "status": current.get("status") or "",
            "sourceText": current.get("sourceText") or "",
        }

    def _resolve_resource(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        team = self._best_current(
            items,
            fields={
                "maxTeamSize",
                "teamSize",
            },
        )

        if team:
            value = self._number(
                team.get("value")
            )

            if value is not None:
                result["resource"] = {
                    "maxTeamSize": int(value),
                    "relation": team.get("relation") or "<=",
                    "role": team.get("role") or "unknown",
                    "status": team.get("status") or "",
                    "sourceText": team.get("sourceText") or "",
                }

    def _resolve_approval(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        # Approval dependencies are intentionally retained even though
        # dependency is not a commercial decision role. They are part of
        # the current decision constraints for downstream reasoning.
        effective = [
            item
            for item in items
            if self._is_runtime_constraint_effective(item)
        ]

        if not effective:
            return

        latest_by_field: dict[str, dict] = {}

        for item in effective:
            key = (
                item.get("field")
                or item.get("target")
                or "approval"
            )
            latest_by_field[key] = item

        result["approval"] = {
            key: {
                "required": True,
                "value": item.get("value"),
                "actor": item.get("actor") or "unknown",
                "role": item.get("role") or "dependency",
                "status": item.get("status") or "",
                "target": item.get("target") or "",
                "sourceText": item.get("sourceText") or "",
            }
            for key, item in latest_by_field.items()
        }

    def _resolve_contract(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        effective = [
            item
            for item in items
            if self._is_runtime_constraint_effective(item)
        ]

        if not effective:
            return

        latest_by_field: dict[str, dict] = {}

        for item in effective:
            key = (
                item.get("field")
                or item.get("kind")
                or "contractTerm"
            )
            latest_by_field[key] = item

        result["contract"] = {
            key: {
                "value": item.get("value"),
                "relation": item.get("relation") or "",
                "role": item.get("role") or "unknown",
                "status": item.get("status") or "",
                "sourceText": item.get("sourceText") or "",
            }
            for key, item in latest_by_field.items()
        }

    def _resolve_decision(
        self,
        result: dict,
        items: list[dict],
    ) -> None:
        effective = [
            item
            for item in items
            if self._is_decision_effective(item)
        ]

        if effective:
            result["decision"] = effective[-1]

    def _best_current(
        self,
        items: list[dict],
        *,
        fields: set[str],
    ) -> dict | None:
        candidates: list[
            tuple[int, int, dict]
        ] = []

        for index, item in enumerate(items):
            if item.get("field") not in fields:
                continue

            if not self._is_decision_effective(item):
                continue

            role = (
                item.get("role")
                or "unknown"
            )

            score = (
                self.ROLE_PRIORITY.get(
                    role,
                    0,
                )
                + self.STATUS_PRIORITY.get(
                    item.get("status") or "",
                    0,
                )
            )

            candidates.append(
                (
                    score,
                    index,
                    item,
                )
            )

        if not candidates:
            return None

        # Semantic priority wins first.
        # List order breaks equal-priority ties in favor of the latest item.
        return max(
            candidates,
            key=lambda entry: (
                entry[0],
                entry[1],
            ),
        )[2]

    def _latest_effective_by_field(
        self,
        items: list[dict],
        field: str,
    ) -> dict | None:
        matched = [
            item
            for item in items
            if (
                item.get("field") == field
                and self._is_decision_effective(item)
            )
        ]

        return matched[-1] if matched else None

    @classmethod
    def _is_decision_effective(
        cls,
        item: dict,
    ) -> bool:
        """Whether an item may become part of decisionState.

        A confirmed customer requirement is still only a requirement.
        'confirmed' describes the certainty of that semantic statement;
        it does not automatically mean the meeting has accepted it.
        """

        if item.get("status") in {
            "withdrawn",
            "rejected",
        }:
            return False

        role = (
            item.get("role")
            or "unknown"
        )

        return role in cls.DECISION_ROLES

    @staticmethod
    def _is_runtime_constraint_effective(
        item: dict,
    ) -> bool:
        """Whether a dependency/liability remains relevant to reasoning."""

        if item.get("status") in {
            "withdrawn",
            "rejected",
        }:
            return False

        role = (
            item.get("role")
            or "unknown"
        )

        # Requirements should not become accepted business decisions,
        # but approval dependencies and liabilities must remain available
        # to the later Active Risk Reasoner.
        return role in {
            "dependency",
            "liability",
            "acceptance",
            "commitment",
            "proposal",
        }

    @staticmethod
    def _number(
        value,
    ) -> float | None:
        if isinstance(
            value,
            (int, float),
        ):
            return float(value)

        if isinstance(
            value,
            str,
        ):
            try:
                return float(value)
            except ValueError:
                return None

        return None


decision_state_resolver = DecisionStateResolver()