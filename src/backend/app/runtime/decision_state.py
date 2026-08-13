from __future__ import annotations

from typing import Any


class DecisionStateResolver:

    """
    Convert semanticState into current effective decision state.

    semanticState:
        all positions from participants

    decisionState:
        only effective execution decision
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
    }



    STATUS_PRIORITY = {

        "confirmed": 50,

        "accepted": 45,

        "pending": 30,

        "proposed": 20,

        "": 0,
    }



    EFFECTIVE_ROLES = {

        "acceptance",

        "commitment",

        "proposal",

    }



    def resolve(
        self,
        semantic_state: dict[str, Any] | None,
    ) -> dict[str, Any]:


        state = semantic_state or {}

        result = {}


        self._resolve_commercial(
            result,
            list(
                state.get(
                    "commercial"
                )
                or []
            ),
        )


        self._resolve_delivery(
            result,
            list(
                state.get(
                    "delivery"
                )
                or []
            ),
        )


        self._resolve_scope(
            result,
            list(
                state.get(
                    "scope"
                )
                or []
            ),
        )


        self._resolve_resource(
            result,
            list(
                state.get(
                    "resource"
                )
                or []
            ),
        )


        self._resolve_approval(
            result,
            list(
                state.get(
                    "approval"
                )
                or []
            ),
        )


        self._resolve_contract(
            result,
            list(
                state.get(
                    "contract"
                )
                or []
            ),
        )


        return result



    def _resolve_commercial(
        self,
        result,
        items,
    ):

        commercial = {}


        discount = self._best_current(
            items,
            {
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
                    discount.get("field")
                    == "priceReduction"
                    and 0 <= value <= 1
                ):
                    value *= 100


                commercial[
                    "discountPercent"
                ] = value



        payment = self._best_current(
            items,
            {
                "paymentTermDays",
                "paymentTerms",
            },
        )


        if payment:

            value = self._number(
                payment.get("value")
            )

            if value is not None:

                commercial[
                    "paymentTermDays"
                ] = int(value)



        if commercial:

            result[
                "commercial"
            ] = commercial



    def _best_current(
        self,
        items,
        fields,
    ):


        candidates = []


        for index, item in enumerate(items):

            if item.get("field") not in fields:
                continue


            if not self._is_effective(item):
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
                +
                self.STATUS_PRIORITY.get(
                    item.get("status")
                    or "",
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


        return max(
            candidates,
            key=lambda x: (
                x[0],
                x[1],
            ),
        )[2]



    @classmethod
    def _is_effective(
        cls,
        item,
    ):


        if item.get("status") in {
            "withdrawn",
            "rejected",
        }:
            return False


        role = (
            item.get("role")
            or "unknown"
        )


        if role in {
            "requirement",
            "assessment",
            "unknown",
        }:
            return False


        return True



    @staticmethod
    def _number(value):

        if isinstance(
            value,
            (int, float),
        ):
            return float(value)


        if isinstance(value, str):

            try:
                return float(value)

            except ValueError:
                return None


        return None



decision_state_resolver = DecisionStateResolver()