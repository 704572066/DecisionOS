from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, TYPE_CHECKING

from app.intervention.models import (
    InterventionDecision,
    InterventionSet,
)
from app.intervention.store import (
    InterventionStore,
    intervention_store,
)
if TYPE_CHECKING:
    from app.reasoning.models import Finding
    from app.reasoning.recommendation_models import Recommendation
    from app.runtime.models import RuntimeState


class InterventionPolicy:
    """Deterministic policy deciding silent / surface / interrupt.

    Important invariant:
        severity != urgency

    A severe Finding is not interrupt-worthy unless delaying the reminder
    is itself risky. Without an explicit high-urgency signal, the policy
    defaults to surface rather than interrupt.
    """

    ACTIVE_FINDING_STATUSES = {"open", "updated", "reopened"}
    ACTIVE_RECOMMENDATION_STATUSES = {"open", "accepted"}

    SEVERITY_WEIGHT = {
        "low": 0.20,
        "medium": 0.50,
        "high": 0.82,
        "critical": 1.00,
    }

    URGENCY_WEIGHT = {
        "low": 0.15,
        "medium": 0.45,
        "high": 0.85,
        "critical": 1.00,
    }

    INTERRUPT_SCORE_THRESHOLD = 0.78
    SURFACE_SCORE_THRESHOLD = 0.42
    INTERRUPT_MIN_CONFIDENCE = 0.75
    INTERRUPT_MIN_RELEVANCE = 0.75
    INTERRUPT_MIN_ACTIONABILITY = 0.60
    DEFAULT_COOLDOWN_SECONDS = 120

    def __init__(
        self,
        *,
        store: InterventionStore | None = None,
        cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
    ) -> None:
        self.store = store if store is not None else intervention_store
        self.cooldown = timedelta(seconds=max(0, cooldown_seconds))

    def evaluate(
        self,
        *,
        state: RuntimeState,
        findings: list[Finding],
        recommendations: list[Recommendation],
        now: datetime | None = None,
    ) -> InterventionSet:
        evaluated_at = now or datetime.now(timezone.utc)
        recommendation_by_finding = self._active_recommendation_map(
            recommendations
        )

        decisions: list[InterventionDecision] = []
        counts = {"silent": 0, "surface": 0, "interrupt": 0}

        for finding in findings:
            recommendation = recommendation_by_finding.get(finding.id)
            decision = self._evaluate_one(
                state=state,
                finding=finding,
                recommendation=recommendation,
                evaluated_at=evaluated_at,
            )
            decisions.append(decision)
            counts[decision.level] += 1

        highest = self._highest_level(decisions)

        return InterventionSet(
            meetingId=state.meetingId,
            contextId=state.contextId,
            decisions=decisions,
            highestLevel=highest,
            evaluatedAt=evaluated_at,
            diagnostics={
                "findingCount": len(findings),
                "decisionCount": len(decisions),
                "interruptCount": counts["interrupt"],
                "surfaceCount": counts["surface"],
                "silentCount": counts["silent"],
                "cooldownSeconds": int(self.cooldown.total_seconds()),
            },
        )

    def _evaluate_one(
        self,
        *,
        state: RuntimeState,
        finding: Finding,
        recommendation: Recommendation | None,
        evaluated_at: datetime,
    ) -> InterventionDecision:
        attrs = dict(finding.attributes or {})
        recommendation_attrs = dict(
            recommendation.attributes or {}
        ) if recommendation is not None else {}

        severity = str(finding.severity or "medium")
        confidence = self._clamp(finding.confidence)
        relevance = self._decision_relevance(
            attrs,
            recommendation_attrs,
        )
        urgency = self._urgency(
            state=state,
            finding_attrs=attrs,
            recommendation_attrs=recommendation_attrs,
        )
        actionability = self._actionability(
            recommendation,
            attrs,
            recommendation_attrs,
        )

        score = self._score(
            severity=severity,
            confidence=confidence,
            decision_relevance=relevance,
            urgency=urgency,
            actionability=actionability,
        )

        fingerprint = (
            finding.fingerprint
            or finding.id
        )

        diagnostics: dict[str, Any] = {
            "components": {
                "severityWeight": self.SEVERITY_WEIGHT.get(severity, 0.5),
                "urgencyWeight": self.URGENCY_WEIGHT.get(urgency, 0.15),
                "confidence": confidence,
                "decisionRelevance": relevance,
                "actionability": actionability,
            },
            "reasoningSource": attrs.get("reasoningSource", "enterprise"),
            "findingType": finding.type,
            "recommendationPresent": recommendation is not None,
        }

        if finding.status not in self.ACTIVE_FINDING_STATUSES:
            level = "silent"
            reason = "inactive_finding"

        else:
            level, reason = self._base_level(
                severity=severity,
                confidence=confidence,
                decision_relevance=relevance,
                urgency=urgency,
                actionability=actionability,
                score=score,
            )

            if level == "interrupt":
                previous = self.store.get(
                    state.meetingId,
                    fingerprint,
                )
                if (
                    previous is not None
                    and previous.lastInterruptAt is not None
                    and evaluated_at - previous.lastInterruptAt < self.cooldown
                ):
                    level = "surface"
                    reason = "interrupt_cooldown_active"
                    diagnostics["cooldownRemainingSeconds"] = max(
                        0,
                        int(
                            (
                                self.cooldown
                                - (evaluated_at - previous.lastInterruptAt)
                            ).total_seconds()
                        ),
                    )

        self.store.put(
            meeting_id=state.meetingId,
            fingerprint=fingerprint,
            level=level,
            evaluated_at=evaluated_at,
        )

        recommendation_id = recommendation.id if recommendation else ""
        message = ""
        if recommendation is not None:
            message = (
                recommendation.action.strip()
                or recommendation.title.strip()
            )
        if not message:
            message = finding.summary.strip() or finding.title.strip()

        return InterventionDecision(
            id=self._decision_id(
                state.meetingId,
                fingerprint,
            ),
            workspaceId=state.workspaceId,
            meetingId=state.meetingId,
            contextId=state.contextId,
            findingId=finding.id,
            recommendationId=recommendation_id,
            level=level,
            reasonCode=reason,
            title=finding.title,
            message=message,
            score=round(score, 6),
            severity=severity,
            urgency=urgency,
            confidence=confidence,
            decisionRelevance=relevance,
            actionability=actionability,
            sourceIds=list(dict.fromkeys([
                *finding.sourceIds,
                *(recommendation.sourceIds if recommendation else []),
            ])),
            fingerprint=f"intervention:{fingerprint}",
            evaluatedAt=evaluated_at,
            diagnostics=diagnostics,
        )

    def _base_level(
        self,
        *,
        severity: str,
        confidence: float,
        decision_relevance: float,
        urgency: str,
        actionability: float,
        score: float,
    ) -> tuple[str, str]:
        severe = severity in {"high", "critical"}
        urgent = urgency in {"high", "critical"}

        if severe and urgent:
            if confidence < self.INTERRUPT_MIN_CONFIDENCE:
                return "surface", "interrupt_blocked_low_confidence"
            if decision_relevance < self.INTERRUPT_MIN_RELEVANCE:
                return "surface", "interrupt_blocked_low_relevance"
            if actionability < self.INTERRUPT_MIN_ACTIONABILITY:
                return "surface", "interrupt_blocked_low_actionability"
            if score < self.INTERRUPT_SCORE_THRESHOLD:
                return "surface", "below_interrupt_threshold"
            return "interrupt", "critical_decision_imminent"

        if score >= self.SURFACE_SCORE_THRESHOLD:
            if severe and not urgent:
                return "surface", "high_severity_low_urgency"
            return "surface", "surface_threshold_met"

        return "silent", "below_surface_threshold"

    def _urgency(
        self,
        *,
        state: RuntimeState,
        finding_attrs: dict[str, Any],
        recommendation_attrs: dict[str, Any],
    ) -> str:
        raw = (
            finding_attrs.get("urgency")
            or recommendation_attrs.get("urgency")
            or ""
        )
        normalized = str(raw).strip().lower()
        if normalized in self.URGENCY_WEIGHT:
            return normalized

        imminent = bool(
            finding_attrs.get("decisionImminent")
            or recommendation_attrs.get("decisionImminent")
            or (state.diagnostics or {}).get("decisionImminent")
            or (state.decisionState or {}).get("decisionImminent")
        )
        return "high" if imminent else "low"

    @staticmethod
    def _decision_relevance(
        finding_attrs: dict[str, Any],
        recommendation_attrs: dict[str, Any],
    ) -> float:
        value = finding_attrs.get(
            "decisionRelevance",
            recommendation_attrs.get("decisionRelevance", 0.8),
        )
        try:
            return InterventionPolicy._clamp(float(value))
        except Exception:
            return 0.8

    @staticmethod
    def _actionability(
        recommendation: Recommendation | None,
        finding_attrs: dict[str, Any],
        recommendation_attrs: dict[str, Any],
    ) -> float:
        raw = finding_attrs.get(
            "actionability",
            recommendation_attrs.get("actionability"),
        )
        if raw is not None:
            try:
                return InterventionPolicy._clamp(float(raw))
            except Exception:
                pass

        if (
            recommendation is not None
            and recommendation.status in InterventionPolicy.ACTIVE_RECOMMENDATION_STATUSES
            and (
                recommendation.action.strip()
                or recommendation.title.strip()
            )
        ):
            return 0.85

        return 0.35

    def _score(
        self,
        *,
        severity: str,
        confidence: float,
        decision_relevance: float,
        urgency: str,
        actionability: float,
    ) -> float:
        severity_weight = self.SEVERITY_WEIGHT.get(severity, 0.5)
        urgency_weight = self.URGENCY_WEIGHT.get(urgency, 0.15)

        return self._clamp(
            0.28 * severity_weight
            + 0.20 * confidence
            + 0.20 * decision_relevance
            + 0.17 * actionability
            + 0.15 * urgency_weight
        )

    def _active_recommendation_map(
        self,
        recommendations: list[Recommendation],
    ) -> dict[str, Recommendation]:
        output: dict[str, Recommendation] = {}
        for item in recommendations:
            if (
                item.status in self.ACTIVE_RECOMMENDATION_STATUSES
                and item.findingId
            ):
                output[item.findingId] = item
        return output

    @staticmethod
    def _highest_level(decisions: list[InterventionDecision]) -> str:
        levels = {item.level for item in decisions}
        if "interrupt" in levels:
            return "interrupt"
        if "surface" in levels:
            return "surface"
        return "silent"

    @staticmethod
    def _decision_id(meeting_id: str, fingerprint: str) -> str:
        digest = hashlib.sha1(
            f"{meeting_id}:{fingerprint}".encode("utf-8")
        ).hexdigest()[:16]
        return f"intervention-{digest}"

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))


intervention_policy = InterventionPolicy()
