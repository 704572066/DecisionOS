from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.reasoning.general.context import (
    GeneralReasoningContext,
    GeneralReasoningSource,
)
from app.reasoning.general.models import (
    GeneralFindingCandidate,
)
from app.reasoning.models import (
    Finding,
    FindingEvidence,
)


@dataclass
class FindingGateDecision:
    accepted: bool
    finding: Finding | None = None
    reason: str = ""
    details: dict[str, Any] = field(
        default_factory=dict
    )


class FindingGate:
    """
    Deterministic authority boundary between LLM candidates and active
    DecisionOS Findings.

    Phase 1.1 adds signal discipline so generic domain checklists and
    weakly grounded observations do not become live Findings.
    """

    TYPE_MAP = {
        "claim": "risk",
        "contradiction": "conflict",
        "missing_information": "gap",
        "uncertainty": "risk",
        "decision_risk": "risk",
    }

    def __init__(
        self,
        *,
        min_confidence: float = 0.68,
        min_decision_relevance: float = 0.75,
        min_specificity: float = 0.65,
        min_evidence_directness: float = 0.60,
        missing_information_min_relevance: float = 0.80,
        missing_information_min_specificity: float = 0.72,
    ) -> None:
        self.min_confidence = min_confidence
        self.min_decision_relevance = min_decision_relevance
        self.min_specificity = min_specificity
        self.min_evidence_directness = min_evidence_directness
        self.missing_information_min_relevance = (
            missing_information_min_relevance
        )
        self.missing_information_min_specificity = (
            missing_information_min_specificity
        )

    def evaluate(
        self,
        context: GeneralReasoningContext,
        candidate: GeneralFindingCandidate,
    ) -> FindingGateDecision:

        if not candidate.title.strip():
            return FindingGateDecision(
                accepted=False,
                reason="missing_title",
            )

        if not candidate.noveltyKey.strip():
            return FindingGateDecision(
                accepted=False,
                reason="missing_novelty_key",
            )

        if candidate.confidence < self.min_confidence:
            return FindingGateDecision(
                accepted=False,
                reason="low_confidence",
                details={
                    "confidence": candidate.confidence,
                    "minimum": self.min_confidence,
                },
            )

        if candidate.type == "missing_information":
            discipline = self._missing_information_discipline(
                candidate
            )
        else:
            discipline = self._observed_signal_discipline(
                candidate
            )

        if discipline is not None:
            return discipline

        source_ids = self._validated_source_ids(
            context,
            candidate,
        )

        authority_decision = self._state_authority_guard(
            context, candidate, source_ids
        )
        if authority_decision is not None:
            return authority_decision

        compatibility_decision = self._semantic_compatibility_guard(
            candidate
        )
        if compatibility_decision is not None:
            return compatibility_decision

        if not source_ids:
            return FindingGateDecision(
                accepted=False,
                reason="ungrounded_candidate",
            )

        fingerprint = self._fingerprint(
            candidate
        )

        evidence = self._evidence(
            context=context,
            source_ids=source_ids,
        )

        finding = Finding(
            id=self._finding_id(
                fingerprint
            ),
            type=self.TYPE_MAP[candidate.type],
            status="open",
            domain=(candidate.domain or "general"),
            subject=(candidate.subject or candidate.type),
            title=candidate.title.strip(),
            summary=candidate.summary.strip(),
            severity=candidate.severity,
            confidence=candidate.confidence,
            sourceIds=source_ids,
            evidence=evidence,
            attributes={
                "reasoningSource": "general",
                "generalFindingType": candidate.type,
                "decisionRelevance": candidate.decisionRelevance,
                "specificity": candidate.specificity,
                "evidenceDirectness": candidate.evidenceDirectness,
                "directlyObserved": candidate.directlyObserved,
                "directlyNeeded": candidate.directlyNeeded,
                "noveltyKey": candidate.noveltyKey,
                "suggestedAction": candidate.suggestedAction,
                **dict(candidate.attributes or {}),
            },
            reasonCode=f"general:{candidate.type}",
            fingerprint=fingerprint,
        )

        return FindingGateDecision(
            accepted=True,
            finding=finding,
            reason="accepted",
            details={
                "validatedSourceIds": source_ids,
                "interventionScore": self.intervention_score(
                    candidate
                ),
            },
        )

    def _observed_signal_discipline(
        self,
        candidate: GeneralFindingCandidate,
    ) -> FindingGateDecision | None:

        if candidate.decisionRelevance < self.min_decision_relevance:
            return FindingGateDecision(
                accepted=False,
                reason="low_decision_relevance",
                details={
                    "decisionRelevance": candidate.decisionRelevance,
                    "minimum": self.min_decision_relevance,
                },
            )

        if candidate.specificity < self.min_specificity:
            return FindingGateDecision(
                accepted=False,
                reason="low_specificity",
                details={
                    "specificity": candidate.specificity,
                    "minimum": self.min_specificity,
                },
            )

        if not candidate.directlyObserved:
            return FindingGateDecision(
                accepted=False,
                reason="not_directly_observed",
            )

        if candidate.evidenceDirectness < self.min_evidence_directness:
            return FindingGateDecision(
                accepted=False,
                reason="low_evidence_directness",
                details={
                    "evidenceDirectness": candidate.evidenceDirectness,
                    "minimum": self.min_evidence_directness,
                },
            )

        return None


    @staticmethod
    def _state_authority_guard(
        context: GeneralReasoningContext,
        candidate: GeneralFindingCandidate,
        source_ids: list[str],
    ) -> FindingGateDecision | None:
        """Do not let conversation/history override structured current state."""
        source_map = context.source_by_id()
        used = [source_map.get(source_id) for source_id in source_ids]
        used = [item for item in used if item is not None]
        uses_conversation = context.contextSourceId in source_ids

        subject = "".join(str(candidate.subject or "").lower().split())
        authoritative_for_subject = []
        for source in context.sources:
            if not bool((source.metadata or {}).get("currentStateAuthority")):
                continue
            field = "".join(str(source.field or "").lower().split())
            if subject and field == subject:
                authoritative_for_subject.append(source)

        if uses_conversation and authoritative_for_subject:
            used_authoritative_ids = {
                source.id for source in used
                if bool((source.metadata or {}).get("currentStateAuthority"))
                and "".join(str(source.field or "").lower().split()) == subject
            }
            if not used_authoritative_ids:
                return FindingGateDecision(
                    accepted=False,
                    reason="conversation_cannot_override_current_state",
                    details={
                        "subject": candidate.subject,
                        "authoritativeSourceIds": [
                            source.id for source in authoritative_for_subject
                        ],
                    },
                )

        return None

    @staticmethod
    def _semantic_compatibility_guard(
        candidate: GeneralFindingCandidate,
    ) -> FindingGateDecision | None:
        """Reject direct comparisons between semantically different metrics."""
        text = " ".join([
            candidate.subject or "",
            candidate.title or "",
            candidate.summary or "",
        ]).lower()
        discount_terms = ("discountpercent", "折扣", "降价")
        margin_terms = ("grossmarginpercent", "毛利率", "利润率")
        has_discount = any(term in text for term in discount_terms)
        has_margin = any(term in text for term in margin_terms)
        conflict_language = any(term in text for term in (
            "冲突", "突破", "低于", "高于", "等于", "直接", "conflict", "below", "above"
        ))
        if (
            candidate.type == "contradiction"
            and has_discount
            and has_margin
            and conflict_language
        ):
            return FindingGateDecision(
                accepted=False,
                reason="incompatible_metric_comparison",
                details={
                    "metrics": ["discountPercent", "grossMarginPercent"],
                    "requirement": "explicit_conversion_or_calculation_required",
                },
            )
        return None

    def _missing_information_discipline(
        self,
        candidate: GeneralFindingCandidate,
    ) -> FindingGateDecision | None:

        if not candidate.directlyNeeded:
            return FindingGateDecision(
                accepted=False,
                reason="generic_missing_information",
                details={
                    "directlyNeeded": False,
                },
            )

        if (
            candidate.decisionRelevance
            < self.missing_information_min_relevance
        ):
            return FindingGateDecision(
                accepted=False,
                reason="low_decision_relevance",
                details={
                    "decisionRelevance": candidate.decisionRelevance,
                    "minimum": self.missing_information_min_relevance,
                },
            )

        if (
            candidate.specificity
            < self.missing_information_min_specificity
        ):
            return FindingGateDecision(
                accepted=False,
                reason="low_specificity",
                details={
                    "specificity": candidate.specificity,
                    "minimum": self.missing_information_min_specificity,
                },
            )

        return None

    @staticmethod
    def intervention_score(
        candidate: GeneralFindingCandidate,
    ) -> float:
        severity_weight = {
            "low": 0.65,
            "medium": 0.82,
            "high": 1.0,
        }.get(candidate.severity, 0.82)

        directness = (
            candidate.evidenceDirectness
            if candidate.type != "missing_information"
            else max(
                0.70,
                candidate.specificity,
            )
        )

        return round(
            candidate.confidence
            * candidate.decisionRelevance
            * candidate.specificity
            * directness
            * severity_weight,
            6,
        )

    @staticmethod
    def _validated_source_ids(
        context: GeneralReasoningContext,
        candidate: GeneralFindingCandidate,
    ) -> list[str]:
        valid_source_ids = context.valid_source_ids()

        source_ids = list(
            dict.fromkeys(
                source_id
                for source_id in candidate.evidenceSourceIds
                if source_id in valid_source_ids
            )
        )

        if not source_ids and context.contextSourceId:
            source_ids = [context.contextSourceId]

        return source_ids

    @staticmethod
    def _fingerprint(
        candidate: GeneralFindingCandidate,
    ) -> str:
        return ":".join(
            [
                "general",
                candidate.type,
                candidate.domain or "_",
                candidate.noveltyKey.strip(),
            ]
        )

    @staticmethod
    def _finding_id(
        fingerprint: str,
    ) -> str:
        digest = hashlib.sha1(
            fingerprint.encode("utf-8")
        ).hexdigest()[:16]
        return f"finding-{digest}"

    @staticmethod
    def _evidence(
        *,
        context: GeneralReasoningContext,
        source_ids: list[str],
    ) -> list[FindingEvidence]:
        source_map = context.source_by_id()
        output: list[FindingEvidence] = []

        for source_id in source_ids:
            if source_id == context.contextSourceId:
                output.append(
                    FindingEvidence(
                        sourceType="runtime",
                        sourceId=source_id,
                        title="Current conversation context",
                        summary=context.canonicalContext,
                        confidence=1.0,
                        metadata={
                            "contextId": context.contextId,
                        },
                    )
                )
                continue

            source = source_map.get(source_id)
            if source is None:
                continue

            output.append(
                FindingGate._source_evidence(
                    source
                )
            )

        return output

    @staticmethod
    def _source_evidence(
        source: GeneralReasoningSource,
    ) -> FindingEvidence:
        allowed = {
            "semantic_state",
            "decision_state",
            "policy",
            "decision",
            "document",
            "crm",
            "runtime",
            "knowledge",
            "other",
        }

        source_type = (
            source.sourceType
            if source.sourceType in allowed
            else "other"
        )

        return FindingEvidence(
            sourceType=source_type,
            sourceId=source.id,
            title=source.title,
            summary=source.summary,
            field=source.field,
            value=source.value,
            actor=source.actor,
            confidence=source.confidence,
            metadata=dict(source.metadata or {}),
        )


finding_gate = FindingGate()
