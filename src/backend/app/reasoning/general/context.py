from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.reasoning.models import Finding
from app.runtime.models import RuntimeState


class GeneralReasoningSource(BaseModel):
    id: str
    sourceType: str = "runtime"
    title: str = ""
    summary: str = ""
    field: str = ""
    value: Any = None
    actor: str = ""
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class GeneralReasoningContext(BaseModel):
    meetingId: str
    contextId: str = ""
    projectId: str = ""

    objective: str = ""
    canonicalContext: str = ""

    semanticState: dict[str, Any] = Field(
        default_factory=dict
    )
    decisionState: dict[str, Any] = Field(
        default_factory=dict
    )
    recentEvents: list[dict[str, Any]] = Field(
        default_factory=list
    )

    # Existing precise policy findings. General Reasoner must avoid
    # restating an issue already covered by these findings.
    activePolicyFindings: list[Finding] = Field(
        default_factory=list
    )

    dialogueHistory: list[dict[str, str]] = Field(
        default_factory=list
    )

    sources: list[GeneralReasoningSource] = Field(
        default_factory=list
    )

    contextSourceId: str = ""

    def source_by_id(self) -> dict[str, GeneralReasoningSource]:
        return {
            item.id: item
            for item in self.sources
            if item.id
        }

    def valid_source_ids(self) -> set[str]:
        output = set(self.source_by_id())
        if self.contextSourceId:
            output.add(self.contextSourceId)
        return output


class GeneralReasoningContextBuilder:
    """
    Build the minimal context needed by General Reasoner.

    Enterprise knowledge is not treated as truth here. Reranked evidence
    is exposed only as source material. General Reasoner focuses on
    decision-relevant signals in the current situation.
    """

    def build(
        self,
        state: RuntimeState,
        *,
        policy_findings: list[Finding] | None = None,
        dialogue_history: list[dict[str, str]] | None = None,
    ) -> GeneralReasoningContext:

        decision_facts = dict(
            state.decisionFacts or {}
        )

        semantic_state = dict(
            decision_facts.get(
                "semanticState",
                {},
            )
            or {}
        )

        active_policy_findings = [
            item
            for item in (policy_findings or [])
            if item.status != "resolved"
        ]

        context_source_id = (
            f"runtime-context:{state.contextId or state.meetingId}"
        )

        sources: list[GeneralReasoningSource] = [
            GeneralReasoningSource(
                id=context_source_id,
                sourceType="runtime",
                title="Current conversation context",
                summary=state.canonicalContext,
                metadata={
                    "meetingId": state.meetingId,
                    "contextId": state.contextId,
                },
            )
        ]

        sources.extend(
            self._event_sources(
                state.recentEvents or []
            )
        )

        sources.extend(
            self._semantic_sources(
                semantic_state
            )
        )

        sources.extend(
            self._retrieval_sources(
                state.rerankedEvidence or []
            )
        )

        return GeneralReasoningContext(
            meetingId=state.meetingId,
            contextId=state.contextId,
            projectId=state.projectId,
            objective=state.objective,
            canonicalContext=state.canonicalContext,
            semanticState=semantic_state,
            decisionState=dict(
                state.decisionState or {}
            ),
            recentEvents=list(
                state.recentEvents or []
            )[-20:],
            activePolicyFindings=(
                active_policy_findings
            ),
            dialogueHistory=list(
                dialogue_history or []
            )[-12:],
            sources=self._dedupe_sources(
                sources
            ),
            contextSourceId=context_source_id,
        )

    @staticmethod
    def _event_sources(
        events: list[dict[str, Any]],
    ) -> list[GeneralReasoningSource]:
        output: list[GeneralReasoningSource] = []

        for event in events[-20:]:
            event_id = str(
                event.get("eventId") or ""
            )
            if not event_id:
                continue

            output.append(
                GeneralReasoningSource(
                    id=event_id,
                    sourceType="runtime",
                    title=str(
                        event.get("type") or "Runtime event"
                    ),
                    summary=str(
                        event.get("sourceText") or ""
                    ),
                    field=str(
                        event.get("field") or ""
                    ),
                    value=event.get("value"),
                    confidence=1.0,
                    metadata=dict(
                        event.get("metadata") or {}
                    ),
                )
            )

        return output

    @staticmethod
    def _semantic_sources(
        semantic_state: dict[str, Any],
    ) -> list[GeneralReasoningSource]:
        output: list[GeneralReasoningSource] = []

        for domain, values in semantic_state.items():
            if not isinstance(values, list):
                continue

            for item in values:
                if not isinstance(item, dict):
                    continue

                source_id = str(
                    item.get("eventId")
                    or item.get("sourceId")
                    or ""
                )
                if not source_id:
                    continue

                output.append(
                    GeneralReasoningSource(
                        id=source_id,
                        sourceType="semantic_state",
                        title=str(
                            item.get("field") or "Semantic state"
                        ),
                        summary=str(
                            item.get("sourceText") or ""
                        ),
                        field=str(
                            item.get("field") or ""
                        ),
                        value=item.get("value"),
                        actor=str(
                            item.get("actor") or ""
                        ),
                        confidence=float(
                            item.get("confidence") or 1.0
                        ),
                        metadata={
                            "domain": domain,
                            "role": item.get("role", ""),
                            "status": item.get("status", ""),
                            "relation": item.get("relation", ""),
                            "kind": item.get("kind", ""),
                            "target": item.get("target", ""),
                        },
                    )
                )

        return output

    @staticmethod
    def _retrieval_sources(
        items: list[dict[str, Any]],
    ) -> list[GeneralReasoningSource]:
        output: list[GeneralReasoningSource] = []

        for item in items[:10]:
            source_id = str(
                item.get("objectId")
                or item.get("itemId")
                or ""
            )
            if not source_id:
                continue

            score = (
                item.get("rerankScore")
                or item.get("score")
                or 0.0
            )

            try:
                confidence = float(score)
            except Exception:
                confidence = 0.0

            output.append(
                GeneralReasoningSource(
                    id=source_id,
                    sourceType=str(
                        item.get("sourceType")
                        or item.get("objectType")
                        or "knowledge"
                    ),
                    title=str(
                        item.get("title") or ""
                    ),
                    summary=str(
                        item.get("summary") or ""
                    ),
                    confidence=max(
                        0.0,
                        min(1.0, confidence),
                    ),
                    metadata={
                        "historicalReference": True,
                    },
                )
            )

        return output

    @staticmethod
    def _dedupe_sources(
        sources: list[GeneralReasoningSource],
    ) -> list[GeneralReasoningSource]:
        output: list[GeneralReasoningSource] = []
        seen: set[str] = set()

        for item in sources:
            if item.id in seen:
                continue
            seen.add(item.id)
            output.append(item)

        return output


general_reasoning_context_builder = (
    GeneralReasoningContextBuilder()
)
