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
    # Sprint 3-3.1 Decision Signal Runtime

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
            currentConditions=dict(state.decisionFacts),
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

    def _risks(self, state: RuntimeState) -> list[BoardRisk]:
        output = []
        seen = set()

        for reminder in state.reminders:
            if reminder.get("type") != "risk":
                continue

            title = (reminder.get("title") or "当前风险").strip()
            summary = (reminder.get("summary") or "").strip()

            if self._is_stale_payment_risk(state, title, summary):
                continue
            if self._is_stale_discount_risk(state, title, summary):
                continue

            title, summary = claim_guard.sanitize_risk(title, summary)
            key = self._norm(title + summary)
            if not key or key in seen:
                continue
            seen.add(key)

            confidence = float(
                reminder.get("confidence")
                or reminder.get("relevanceScore")
                or 0
            )
            severity = (
                "high" if confidence >= .85
                else "medium" if confidence >= .6
                else "low"
            )
            source_ids = [
                str(item.get("id"))
                for item in (reminder.get("sources") or [])
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

        # Runtime facts are the source of truth for conditions that are still
        # active. A reminder may disappear (or be filtered as stale) after a
        # payment change, but an 18% discount must remain visible until the
        # discount itself changes.
        discount = state.decisionFacts.get("discountPercent")
        if (
            discount is not None
            and float(discount) > 10
            and "discount" not in state.resolvedRiskKeys
            and not self._has_price_risk(output)
        ):
            value = float(discount)
            output.append(
                BoardRisk(
                    title=f"{value:g}%折扣需要重点评估",
                    summary=(
                        f"当前折扣为{value:g}%，已超过公司10%的折扣评估门槛；"
                        "折扣会影响项目利润，是否满足目标毛利率仍需结合项目成本测算。"
                    ),
                    severity="high",
                    sourceIds=self._policy_source_ids(state),
                )
            )

        order = {"high": 3, "medium": 2, "low": 1}
        output.sort(key=lambda item: order[item.severity], reverse=True)
        return output

    def _evidence(self, state):
        output = []
        seen = set()
        for item in state.rerankedEvidence:
            object_id = str(
                item.get("objectId") or item.get("itemId") or ""
            )
            if not object_id or object_id in seen:
                continue
            seen.add(object_id)
            output.append(
                BoardEvidence(
                    id=object_id,
                    type=item.get("sourceType")
                    or item.get("objectType")
                    or "knowledge",
                    title=item.get("title") or "企业依据",
                    summary=item.get("summary") or "",
                    score=float(
                        item.get("rerankScore")
                        or item.get("score")
                        or 0
                    ),
                )
            )
        output.sort(key=lambda item: item.score, reverse=True)
        return output

    def _actions(self, state):
        output = []
        seen = set()
        for reminder in state.reminders:
            suggestion = (reminder.get("suggestion") or "").strip()
            if not suggestion:
                continue
            reminder_title = reminder.get("title") or ""
            reminder_text = (reminder.get("summary") or "") + " " + suggestion
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
            key = self._norm(suggestion)
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(
                BoardAction(
                    text=suggestion,
                    sourceIds=[
                        str(item.get("id"))
                        for item in (reminder.get("sources") or [])
                        if item.get("id")
                    ][:3],
                )
            )
        return output

    @staticmethod
    def _has_price_risk(risks: list[BoardRisk]) -> bool:
        terms = ("折扣", "降价", "价格", "利润", "毛利")
        return any(
            any(term in (risk.title + " " + risk.summary) for term in terms)
            for risk in risks
        )

    @staticmethod
    def _policy_source_ids(state: RuntimeState) -> list[str]:
        output = []
        for item in state.rerankedEvidence:
            source_type = item.get("sourceType") or item.get("objectType")
            if source_type != "policy":
                continue
            object_id = item.get("objectId") or item.get("itemId")
            if object_id:
                output.append(str(object_id))
        return output[:3]

    @staticmethod
    def _readiness(state, evidence):
        score = (
            20
            + (15 if state.objective else 0)
            + (10 if state.canonicalContext else 0)
            + min(15, len(state.facts) * 5)
            + min(25, len(evidence) * 6)
            + (7 if any(item.type == "policy" for item in evidence) else 0)
            + (5 if any(item.type == "decision" for item in evidence) else 0)
            + (5 if state.reminders else 0)
        )
        return max(0, min(100, round(score)))

    @staticmethod
    def _status(state, risks, readiness):
        if not state.canonicalContext or readiness < 45:
            return "gathering_information"
        if any(item.severity == "high" for item in risks):
            return "negotiating"
        if readiness >= 80 and state.reminders:
            return "ready_to_decide"
        return "waiting_confirmation"

    @staticmethod
    def _is_stale_payment_risk(
        state: RuntimeState,
        title: str,
        summary: str,
    ) -> bool:
        if "payment_term" not in state.resolvedRiskKeys:
            return False

        current = state.decisionFacts.get("paymentTermDays")
        if current is None:
            return False

        text = title + " " + summary
        old_days = [
            int(value)
            for value in re.findall(r"(\d+)\s*天", text)
        ]
        return any(value > int(current) for value in old_days)

    @staticmethod
    def _is_stale_discount_risk(
        state: RuntimeState,
        title: str,
        summary: str,
    ) -> bool:
        if "discount" not in state.resolvedRiskKeys:
            return False

        current = state.decisionFacts.get("discountPercent")
        if current is None:
            return False

        # Use the reminder title to identify its primary risk. Summaries often
        # contain policy/history percentages (for example 10% or 8%), which
        # must not be mistaken for the current negotiated discount.
        title_text = title or ""
        if not any(
            term in title_text
            for term in ("折扣", "降价", "价格", "利润率", "毛利率")
        ):
            return False

        percentages = [
            float(value)
            for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", title_text)
        ]
        if not percentages:
            return True

        return any(value > float(current) for value in percentages)

    @staticmethod
    def _norm(text):
        return re.sub(
            r"[\s，。；：、,.!?！？:;]+",
            "",
            text,
        ).lower()


decision_board_engine = DecisionBoardEngine()
