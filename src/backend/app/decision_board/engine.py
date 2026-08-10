from __future__ import annotations

import re

from app.decision_board.claim_guard import claim_guard
from app.decision_board.models import (
    BoardAction,
    BoardEvidence,
    BoardRisk,
    BoardTodo,
    DecisionBoard,
)
from app.runtime.models import RuntimeState


class DecisionBoardEngine:
    # Sprint 3-3.1 Decision Signal Runtime

    def build(self, state: RuntimeState) -> DecisionBoard:
        risks = self._risks(state)
        evidence = self._evidence(state)
        actions = self._actions(state)
        todos = self._todos(state, risks)
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
            todos=todos[:5],
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
            if self._is_stale_payment_risk(
                state,
                reminder.get("title") or "",
                (reminder.get("summary") or "") + " " + suggestion,
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

    def _todos(self, state, risks):
        output = []
        seen = set()

        def add(text, reason):
            key = self._norm(text)
            if key and key not in seen:
                seen.add(key)
                output.append(BoardTodo(text=text, reason=reason))

        if any(topic in state.topics for topic in ("价格", "利润")):
            add(
                "确认当前方案的最低可接受毛利率与折扣边界",
                "当前会议涉及价格/利润条件。",
            )

        payment_days = state.decisionFacts.get("paymentTermDays")
        if "付款" in state.topics:
            if payment_days is not None:
                add(
                    f"确认当前{payment_days}天付款周期对应的风险控制条件",
                    "付款条件已发生结构化更新。",
                )
            else:
                add(
                    "确认可接受付款周期及对应风险控制条件",
                    "当前会议涉及付款周期。",
                )

        for runtime_constraint in (
            state.decisionFacts.get("runtimeConstraints") or []
        ):
            add(
                "确认约束：" + runtime_constraint,
                "会议中新增了约束条件。",
            )

        if any(item.severity == "high" for item in risks):
            add(
                "由负责人确认是否继续按当前条件推进谈判",
                "当前存在高优先级风险，AI 不替代最终决策。",
            )

        return output

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
    def _norm(text):
        return re.sub(
            r"[\s，。；：、,.!?！？:;]+",
            "",
            text,
        ).lower()


decision_board_engine = DecisionBoardEngine()
