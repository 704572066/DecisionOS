from __future__ import annotations

from typing import Any

from app.runtime.semantic_policy import semantic_policy



class DecisionStateResolver:
    """
    Resolve semanticState into effective decisionState.

    semanticState:
        current semantic memory

    decisionState:
        executable decision surface

    Governance rules are delegated to semantic_policy.
    """



    def resolve(
        self,
        semantic_state:dict[str,Any] | None,
    )->dict[str,Any]:

        state = semantic_state or {}

        result={}


        self._resolve_commercial(
            result,
            list(state.get("commercial") or [])
        )


        self._resolve_delivery(
            result,
            list(state.get("delivery") or [])
        )


        self._resolve_scope(
            result,
            list(state.get("scope") or [])
        )


        self._resolve_resource(
            result,
            list(state.get("resource") or [])
        )


        self._resolve_approval(
            result,
            list(state.get("approval") or [])
        )


        self._resolve_contract(
            result,
            list(state.get("contract") or [])
        )


        self._resolve_decision(
            result,
            list(state.get("decision") or [])
        )


        return result



    def _resolve_commercial(
        self,
        result,
        items,
    ):

        commercial={}


        discount=self._best_current(
            items,
            {
                "discountPercent",
                "priceReduction",
            }
        )


        if discount:

            value=self._number(
                discount.get("value")
            )

            if value is not None:

                if (
                    discount.get("field")
                    =="priceReduction"
                    and 0<=value<=1
                ):
                    value=value*100


                commercial[
                    "discountPercent"
                ]=value



        payment=self._best_current(
            items,
            {
                "paymentTermDays",
                "paymentTerms",
            }
        )


        if payment:

            value=self._number(
                payment.get("value")
            )

            if value is not None:

                commercial[
                    "paymentTermDays"
                ]=int(value)



        if commercial:

            result["commercial"]=commercial





    def _resolve_delivery(
        self,
        result,
        items,
    ):

        selected=self._best_current(
            items,
            {
                "goLiveDate",
                "deliveryDate",
                "deadline",
            }
        )


        if selected:

            result["delivery"]={

                "goLiveDate":
                    selected.get("value"),

                "relation":
                    selected.get("relation")
                    or "",

                "role":
                    selected.get("role")
                    or "unknown",

                "status":
                    selected.get("status")
                    or "",

                "sourceText":
                    selected.get("sourceText")
                    or "",
            }





    def _resolve_scope(
        self,
        result,
        items,
    ):

        current=None


        for item in items:

            if (
                item.get("field")
                =="scopeInclusion"
                and semantic_policy
                    .is_decision_effective(item)
            ):
                current=item



        if current:

            result["scope"]={

                "field":
                    current.get("field"),

                "value":
                    current.get("value"),

                "relation":
                    current.get("relation")
                    or "",

                "role":
                    current.get("role")
                    or "",

                "status":
                    current.get("status")
                    or "",

                "sourceText":
                    current.get("sourceText")
                    or "",
            }





    def _resolve_resource(
        self,
        result,
        items,
    ):

        team=self._best_current(
            items,
            {
                "maxTeamSize",
                "teamSize",
            }
        )


        if team:

            value=self._number(
                team.get("value")
            )

            if value is not None:

                result["resource"]={

                    "maxTeamSize":
                        int(value),

                    "relation":
                        team.get("relation")
                        or "<=",

                    "role":
                        team.get("role")
                        or "",

                    "status":
                        team.get("status")
                        or "",
                }






    def _resolve_approval(
        self,
        result,
        items,
    ):


        effective=[

            item
            for item in items

            if semantic_policy
                .is_runtime_constraint_effective(item)

        ]


        if not effective:
            return



        result["approval"]={}


        for item in effective:

            key=(
                item.get("field")
                or item.get("target")
                or "approval"
            )


            result["approval"][key]={

                "required":
                    True,

                "value":
                    item.get("value"),

                "actor":
                    item.get("actor")
                    or "unknown",

                "role":
                    item.get("role")
                    or "",

                "status":
                    item.get("status")
                    or "",

                "target":
                    item.get("target")
                    or "",

                "sourceText":
                    item.get("sourceText")
                    or "",
            }





    def _resolve_contract(
        self,
        result,
        items,
    ):


        effective=[

            item
            for item in items

            if semantic_policy
                .is_runtime_constraint_effective(item)

        ]


        if not effective:
            return



        result["contract"]={}


        for item in effective:

            key=(
                item.get("field")
                or item.get("kind")
                or "contractTerm"
            )


            result["contract"][key]={

                "value":
                    item.get("value"),

                "relation":
                    item.get("relation")
                    or "",

                "role":
                    item.get("role")
                    or "",

                "status":
                    item.get("status")
                    or "",

                "sourceText":
                    item.get("sourceText")
                    or "",
            }





    def _resolve_decision(
        self,
        result,
        items,
    ):

        effective=[

            item
            for item in items

            if semantic_policy
                .is_decision_effective(item)

        ]


        if effective:

            result["decision"]=effective[-1]





    def _best_current(
        self,
        items,
        fields:set[str],
    ):


        candidates=[]


        for index,item in enumerate(items):

            if item.get("field") not in fields:
                continue


            if not semantic_policy.is_decision_effective(item):
                continue



            score=semantic_policy.semantic_score(
                item
            )


            candidates.append(
                (
                    score,
                    index,
                    item
                )
            )



        if not candidates:
            return None



        return max(
            candidates,
            key=lambda x:(x[0],x[1])
        )[2]





    @staticmethod
    def _number(value):

        if isinstance(value,(int,float)):
            return float(value)


        if isinstance(value,str):

            try:
                return float(value)

            except ValueError:
                return None


        return None




decision_state_resolver = DecisionStateResolver()