from __future__ import annotations

import re

from app.decision_board.claim_guard import claim_guard
from app.decision_board.models import (
    BoardAction,
    BoardEvidence,
    BoardRisk,
    DecisionBoard,
)
from app.runtime.models import RuntimeState


class DecisionBoardEngine:
    # Sprint 3-3.4.1 Current Condition Authority Consolidation
    #
    # Runtime fast facts:
    #   state.decisionFacts
    #
    # Semantic participant positions:
    #   state.decisionFacts["semanticState"]
    #
    # Current effective decision surface:
    #   state.decisionState
    #
    # Decision Board must expose decisionState as the authority for
    # "current effective conditions". Runtime facts remain internal
    # telemetry/fallback for legacy lifecycle logic only.

    def build(self, state: RuntimeState) -> DecisionBoard:
        risks = self._risks(state)
        evidence = self._evidence(state)
        actions = self._actions(state)
        readiness = self._readiness(state, evidence)
        status = self._status(state, risks, readiness)

        return DecisionBoard(
            meetingId=state.meetingId,
            projectId=state.projectId,
            contextId=state.contextId,
            objective=state.objective,
            status=status,
            decisionReadiness=readiness,
            risks=risks[:3],
            evidence=evidence[:5],
            actions=actions[:3],
            currentConditions=self._current_conditions(state),
            recentEvents=list(state.recentEvents[-6:]),
            resolvedRisks=list(state.resolvedRiskKeys),
            updatedAt=state.updatedAt,
            diagnostics={
                "retrievalMode": state.retrievalMode,
                "reminderCount": len(state.reminders),
                "evidenceCount": len(state.rerankedEvidence),
                "eventCount": len(state.recentEvents),
            },
        )

    @staticmethod
    def _current_conditions(
        state: RuntimeState,
    ) -> dict:
        """
        Build user-visible current conditions.

        decisionState is the authority.

        decisionFacts are intentionally NOT expanded into this object,
        because values such as discountPercent/paymentTermDays may represent
        the last structured runtime observation instead of an effective
        decision accepted by the current semantic state.
        """

        decision_state = dict(
            state.decisionState or {}
        )

        semantic_state = dict(
            state.decisionFacts.get("semanticState")
            or {}
        )

        output = {
            "decisionState": decision_state,
            "semanticState": semantic_state,
        }

        # Backward-compatible flat fields for the current frontend.
        # IMPORTANT: only expose them when decisionState actually contains
        # an effective commercial condition.
        commercial = (
            decision_state.get("commercial")
            or {}
        )

        discount = commercial.get(
            "discountPercent"
        )

        if discount is not None:
            output["discountPercent"] = discount

        payment_days = commercial.get(
            "paymentTermDays"
        )

        if payment_days is not None:
            output["paymentTermDays"] = payment_days

        return output

    def _risks(
        self,
        state: RuntimeState,
    ) -> list[BoardRisk]:
        output = []
        seen = set()

        for reminder in state.reminders:
            if reminder.get("type") != "risk":
                continue

            title = (
                reminder.get("title")
                or "当前风险"
            ).strip()

            summary = (
                reminder.get("summary")
                or ""
            ).strip()

            if self._is_stale_payment_risk(
                state,
                title,
                summary,
            ):
                continue

            if self._is_stale_discount_risk(
                state,
                title,
                summary,
            ):
                continue

            title, summary = (
                claim_guard.sanitize_risk(
                    title,
                    summary,
                )
            )

            key = self._norm(
                title + summary
            )

            if (
                not key
                or key in seen
            ):
                continue

            seen.add(key)

            confidence = float(
                reminder.get("confidence")
                or reminder.get("relevanceScore")
                or 0
            )

            severity = (
                "high"
                if confidence >= .85
                else "medium"
                if confidence >= .6
                else "low"
            )

            source_ids = [
                str(item.get("id"))
                for item in (
                    reminder.get("sources")
                    or []
                )
                if item.get("id")
            ]

            output.append(
                BoardRisk(
                    title=title,
                    summary=summary,
                    severity=severity,
                    sourceIds=source_ids[:3],
                )
            )

        #
        # Sprint 3-3.4.1
        #
        # Do NOT use decisionFacts.discountPercent as the current negotiated
        # decision anymore.
        #
        # Only an effective semantic decision may generate this runtime
        # current-condition fallback risk.
        #
        current_discount = self._effective_discount(
            state
        )

        if (
            current_discount is not None
            and current_discount > 10
            and "discount"
            not in state.resolvedRiskKeys
            and not self._has_price_risk(output)
        ):
            output.append(
                BoardRisk(
                    title=(
                        f"{current_discount:g}%折扣需要重点评估"
                    ),
                    summary=(
                        f"当前有效折扣条件为"
                        f"{current_discount:g}%，"
                        "已超过公司10%的折扣评估门槛；"
                        "折扣会影响项目利润，"
                        "是否满足目标毛利率仍需结合项目成本测算。"
                    ),
                    severity="high",
                    sourceIds=self._policy_source_ids(
                        state
                    ),
                )
            )

        order = {
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        output.sort(
            key=lambda item: order[
                item.severity
            ],
            reverse=True,
        )

        return output

    def _evidence(
        self,
        state: RuntimeState,
    ):
        output = []
        seen = set()

        for item in state.rerankedEvidence:
            object_id = str(
                item.get("objectId")
                or item.get("itemId")
                or ""
            )

            if (
                not object_id
                or object_id in seen
            ):
                continue

            seen.add(object_id)

            output.append(
                BoardEvidence(
                    id=object_id,
                    type=(
                        item.get("sourceType")
                        or item.get("objectType")
                        or "knowledge"
                    ),
                    title=(
                        item.get("title")
                        or "企业依据"
                    ),
                    summary=(
                        item.get("summary")
                        or ""
                    ),
                    score=float(
                        item.get("rerankScore")
                        or item.get("score")
                        or 0
                    ),
                )
            )

        output.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return output

    def _actions(
        self,
        state: RuntimeState,
    ):
        output = []
        seen = set()

        for reminder in state.reminders:
            suggestion = (
                reminder.get("suggestion")
                or ""
            ).strip()

            if not suggestion:
                continue

            reminder_title = (
                reminder.get("title")
                or ""
            )

            reminder_text = (
                (reminder.get("summary") or "")
                + " "
                + suggestion
            )

            if self._is_stale_payment_risk(
                state,
                reminder_title,
                reminder_text,
            ):
                continue

            if self._is_stale_discount_risk(
                state,
                reminder_title,
                reminder_text,
            ):
                continue

            key = self._norm(
                suggestion
            )

            if (
                not key
                or key in seen
            ):
                continue

            seen.add(key)

            output.append(
                BoardAction(
                    text=suggestion,
                    sourceIds=[
                        str(item.get("id"))
                        for item in (
                            reminder.get("sources")
                            or []
                        )
                        if item.get("id")
                    ][:3],
                )
            )

        return output

    @staticmethod
    def _effective_commercial(
        state: RuntimeState,
    ) -> dict:
        return dict(
            (
                state.decisionState
                or {}
            ).get("commercial")
            or {}
        )

    @classmethod
    def _effective_discount(
        cls,
        state: RuntimeState,
    ) -> float | None:
        value = cls._effective_commercial(
            state
        ).get("discountPercent")

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _effective_payment_days(
        cls,
        state: RuntimeState,
    ) -> int | None:
        value = cls._effective_commercial(
            state
        ).get("paymentTermDays")

        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _has_price_risk(
        risks: list[BoardRisk],
    ) -> bool:
        terms = (
            "折扣",
            "降价",
            "价格",
            "利润",
            "毛利",
        )

        return any(
            any(
                term
                in (
                    risk.title
                    + " "
                    + risk.summary
                )
                for term in terms
            )
            for risk in risks
        )

    @staticmethod
    def _policy_source_ids(
        state: RuntimeState,
    ) -> list[str]:
        output = []

        for item in state.rerankedEvidence:
            source_type = (
                item.get("sourceType")
                or item.get("objectType")
            )

            if source_type != "policy":
                continue

            object_id = (
                item.get("objectId")
                or item.get("itemId")
            )

            if object_id:
                output.append(
                    str(object_id)
                )

        return output[:3]

    @staticmethod
    def _readiness(
        state,
        evidence,
    ):
        score = (
            20
            + (15 if state.objective else 0)
            + (
                10
                if state.canonicalContext
                else 0
            )
            + min(
                15,
                len(state.facts) * 5,
            )
            + min(
                25,
                len(evidence) * 6,
            )
            + (
                7
                if any(
                    item.type == "policy"
                    for item in evidence
                )
                else 0
            )
            + (
                5
                if any(
                    item.type == "decision"
                    for item in evidence
                )
                else 0
            )
            + (
                5
                if state.reminders
                else 0
            )
        )

        return max(
            0,
            min(
                100,
                round(score),
            ),
        )

    @staticmethod
    def _status(
        state,
        risks,
        readiness,
    ):
        if (
            not state.canonicalContext
            or readiness < 45
        ):
            return "gathering_information"

        if any(
            item.severity == "high"
            for item in risks
        ):
            return "negotiating"

        if (
            readiness >= 80
            and state.reminders
        ):
            return "ready_to_decide"

        return "waiting_confirmation"

    @classmethod
    def _is_stale_payment_risk(
        cls,
        state: RuntimeState,
        title: str,
        summary: str,
    ) -> bool:
        """
        A payment reminder is stale only when we have an effective
        current payment decision that contradicts the older reminder.

        resolvedRiskKeys is retained for compatibility, but the current
        value must come from decisionState.
        """

        if (
            "payment_term"
            not in state.resolvedRiskKeys
        ):
            return False

        current = (
            cls._effective_payment_days(
                state
            )
        )

        # If there is no effective payment decision anymore,
        # do NOT claim that an old reminder is stale merely because a
        # Rule Runtime fact exists.
        if current is None:
            return False

        text = (
            title
            + " "
            + summary
        )

        old_days = [
            int(value)
            for value in re.findall(
                r"(\d+)\s*天",
                text,
            )
        ]

        return any(
            value > current
            for value in old_days
        )

    @classmethod
    def _is_stale_discount_risk(
        cls,
        state: RuntimeState,
        title: str,
        summary: str,
    ) -> bool:
        """
        Determine staleness against the effective decisionState discount,
        never against raw Rule Runtime discountPercent.
        """

        if (
            "discount"
            not in state.resolvedRiskKeys
        ):
            return False

        current = cls._effective_discount(
            state
        )

        # No active semantic discount decision means there is no newer
        # effective condition we can use to invalidate a reminder.
        if current is None:
            return False

        title_text = (
            title
            or ""
        )

        if not any(
            term in title_text
            for term in (
                "折扣",
                "降价",
                "价格",
                "利润率",
                "毛利率",
            )
        ):
            return False

        percentages = [
            float(value)
            for value in re.findall(
                r"(\d+(?:\.\d+)?)\s*%",
                title_text,
            )
        ]

        if not percentages:
            return True

        return any(
            value > current
            for value in percentages
        )

    @staticmethod
    def _norm(
        text,
    ):
        return re.sub(
            r"[\s，。；：、,.!?！？:;]+",
            "",
            text,
        ).lower()


decision_board_engine = DecisionBoardEngine()