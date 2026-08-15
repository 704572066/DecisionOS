from __future__ import annotations

from datetime import datetime, timezone

from app.decision_board.models import (
    BoardAction,
    BoardEvidence,
    BoardRisk,
    DecisionBoard,
    DecisionBoardReasoning,
)
from app.decision_board.reasoning_adapter import (
    reasoning_decision_board_adapter,
)
from app.reasoning.models import ReasoningResult
from app.runtime.models import RuntimeState


class DecisionBoardBuilder:
    """
    Pure DecisionBoard projection.

    IMPORTANT:
    This builder performs no business reasoning.

    Authority:
        RuntimeState       -> context/evidence/runtime projection
        ReasoningResult    -> risks/actions/reasoning projection

    It must not contain:
        - business thresholds
        - field-specific risk rules
        - keyword-based policy interpretation
        - hard-coded commercial logic
    """

    def build(
        self,
        *,
        state: RuntimeState,
        reasoning: ReasoningResult,
    ) -> DecisionBoard:

        projection = (
            reasoning_decision_board_adapter.project(
                findings=reasoning.findings,
                recommendations=(
                    reasoning.recommendations
                ),
            )
        )

        evidence = self._evidence(
            state
        )

        current_conditions = {
            "decisionState": dict(
                state.decisionState or {}
            ),
            "semanticState": dict(
                (
                    state.decisionFacts
                    or {}
                ).get(
                    "semanticState",
                    {},
                )
                or {}
            ),
        }

        reasoning_diagnostics = (
            reasoning.diagnostics.model_dump(
                mode="json"
            )
            if hasattr(
                reasoning.diagnostics,
                "model_dump",
            )
            else reasoning.diagnostics
        )

        status = self._status(
            state=state,
            reasoning=reasoning,
        )

        readiness = self._decision_readiness(
            reasoning
        )

        return DecisionBoard(
            meetingId=state.meetingId,
            projectId=state.projectId,
            contextId=state.contextId,

            reasoning=DecisionBoardReasoning(
                findings=reasoning.findings,
                constraints=reasoning.constraints,
                recommendations=(
                    reasoning.recommendations
                ),
                diagnostics=(
                    reasoning_diagnostics
                ),
            ),

            objective=state.objective,

            status=status,

            decisionReadiness=readiness,

            risks=projection.risks,

            evidence=evidence,

            actions=projection.actions,

            currentConditions=(
                current_conditions
            ),

            recentEvents=list(
                state.recentEvents or []
            ),

            resolvedRisks=self._resolved_risks(
                reasoning
            ),

            updatedAt=datetime.now(
                timezone.utc
            ),

            diagnostics={
                "retrievalMode": (
                    state.retrievalMode
                ),
                "evidenceCount": len(
                    evidence
                ),
                "eventCount": len(
                    state.recentEvents or []
                ),
                "reasoningRiskCount": len(
                    projection.risks
                ),
                "reasoningActionCount": len(
                    projection.actions
                ),
                "reasoningAdapter": (
                    projection.diagnostics
                ),
            },
        )

    @staticmethod
    def _evidence(
        state: RuntimeState,
    ) -> list[BoardEvidence]:

        output: list[BoardEvidence] = []

        seen: set[str] = set()

        for item in list(
            state.rerankedEvidence or []
        ):
            object_id = str(
                item.get("objectId")
                or item.get("itemId")
                or ""
            )

            if not object_id:
                continue

            if object_id in seen:
                continue

            seen.add(
                object_id
            )

            output.append(
                BoardEvidence(
                    id=object_id,
                    type=str(
                        item.get(
                            "sourceType"
                        )
                        or item.get(
                            "objectType"
                        )
                        or "knowledge"
                    ),
                    title=str(
                        item.get(
                            "title"
                        )
                        or ""
                    ),
                    summary=str(
                        item.get(
                            "summary"
                        )
                        or ""
                    ),
                    score=float(
                        item.get(
                            "rerankScore"
                        )
                        or item.get(
                            "score"
                        )
                        or 0.0
                    ),
                )
            )

        return output

    @staticmethod
    def _status(
        *,
        state: RuntimeState,
        reasoning: ReasoningResult,
    ) -> str:
        """
        Minimal generic status projection.

        This is not a business rule engine.
        """

        active_findings = [
            item
            for item in reasoning.findings
            if item.status == "open"
        ]

        if active_findings:
            return "gathering_information"

        if state.decisionState:
            return "decision_ready"

        return "negotiating"

    @staticmethod
    def _decision_readiness(
        reasoning: ReasoningResult,
    ) -> int:
        """
        Temporary generic readiness projection.

        Avoid field-specific scoring.

        Later this should become a dedicated Readiness Reasoner.
        """

        active = [
            item
            for item in reasoning.findings
            if item.status == "open"
        ]

        if not active:
            return 100

        severity_weight = {
            "critical": 30,
            "high": 20,
            "medium": 10,
            "low": 5,
        }

        penalty = sum(
            severity_weight.get(
                item.severity,
                10,
            )
            for item in active
        )

        return max(
            0,
            100 - min(
                80,
                penalty,
            ),
        )

    @staticmethod
    def _resolved_risks(
        reasoning: ReasoningResult,
    ) -> list[str]:

        return [
            item.fingerprint
            for item in reasoning.findings
            if item.status == "resolved"
        ]


decision_board_builder = (
    DecisionBoardBuilder()
)
