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

    Phase 1 deliberately keeps the gate simple and inspectable.
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
        min_confidence: float = 0.65,
        min_decision_relevance: float = 0.70,
    ) -> None:
        self.min_confidence = min_confidence
        self.min_decision_relevance = (
            min_decision_relevance
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

        if (
            candidate.confidence
            < self.min_confidence
        ):
            return FindingGateDecision(
                accepted=False,
                reason="low_confidence",
                details={
                    "confidence": candidate.confidence,
                    "minimum": self.min_confidence,
                },
            )

        if (
            candidate.decisionRelevance
            < self.min_decision_relevance
        ):
            return FindingGateDecision(
                accepted=False,
                reason="low_decision_relevance",
                details={
                    "decisionRelevance": (
                        candidate.decisionRelevance
                    ),
                    "minimum": (
                        self.min_decision_relevance
                    ),
                },
            )

        valid_source_ids = (
            context.valid_source_ids()
        )

        source_ids = list(
            dict.fromkeys(
                source_id
                for source_id
                in candidate.evidenceSourceIds
                if source_id
                in valid_source_ids
            )
        )

        if not source_ids:
            # The current-context source is a legitimate grounding anchor,
            # especially for missing-information candidates.
            source_ids = [
                context.contextSourceId
            ] if context.contextSourceId else []

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
            type=self.TYPE_MAP[
                candidate.type
            ],
            status="open",
            domain=(
                candidate.domain
                or "general"
            ),
            subject=(
                candidate.subject
                or candidate.type
            ),
            title=candidate.title.strip(),
            summary=candidate.summary.strip(),
            severity=candidate.severity,
            confidence=candidate.confidence,
            sourceIds=source_ids,
            evidence=evidence,
            attributes={
                "reasoningSource": "general",
                "generalFindingType": (
                    candidate.type
                ),
                "decisionRelevance": (
                    candidate.decisionRelevance
                ),
                "noveltyKey": (
                    candidate.noveltyKey
                ),
                "suggestedAction": (
                    candidate.suggestedAction
                ),
                **dict(
                    candidate.attributes or {}
                ),
            },
            reasonCode=(
                f"general:{candidate.type}"
            ),
            fingerprint=fingerprint,
        )

        return FindingGateDecision(
            accepted=True,
            finding=finding,
            reason="accepted",
            details={
                "validatedSourceIds": source_ids,
            },
        )

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
            if (
                source_id
                == context.contextSourceId
            ):
                output.append(
                    FindingEvidence(
                        sourceType="runtime",
                        sourceId=source_id,
                        title="Current conversation context",
                        summary=(
                            context.canonicalContext
                        ),
                        confidence=1.0,
                        metadata={
                            "contextId": context.contextId,
                        },
                    )
                )
                continue

            source = source_map.get(
                source_id
            )
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
            metadata=dict(
                source.metadata or {}
            ),
        )


finding_gate = FindingGate()
