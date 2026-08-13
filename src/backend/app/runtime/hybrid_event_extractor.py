from __future__ import annotations

from uuid import uuid4

from app.runtime.event_extractor import event_extractor
from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState
from app.runtime.semantic_event_extractor import (
    semantic_event_extractor,
)
from app.runtime.semantic_models import (
    SemanticEventCandidate,
)


class HybridEventExtractor:
    """Combine deterministic runtime events and semantic decision events.

    Rule events maintain fast structured facts such as discountPercent and
    paymentTermDays.

    Semantic events maintain meaning such as requirement, proposal,
    commitment, acceptance and dependency.

    Both event types may legitimately describe the same transcript segment
    and therefore must coexist.
    """

    async def extract(
        self,
        meeting_id: str,
        text: str,
        previous: RuntimeState | None,
        *,
        semantic_enabled: bool = True,
        meeting_date=None,
    ) -> list[DecisionEvent]:

        rule_events = event_extractor.extract(
            meeting_id,
            text,
            previous,
        )

        if not semantic_enabled:
            return rule_events

        semantic_kwargs = (
            {"meeting_date": meeting_date}
            if meeting_date is not None
            else {}
        )

        semantic = await semantic_event_extractor.extract(
            text,
            previous,
            **semantic_kwargs,
        )

        semantic_events = [
            self._to_runtime_event(
                meeting_id,
                event,
            )
            for event in semantic
        ]

        return self._dedupe(
            [
                *rule_events,
                *semantic_events,
            ]
        )

    @staticmethod
    def _to_runtime_event(
        meeting_id: str,
        event: SemanticEventCandidate,
    ) -> DecisionEvent:

        return DecisionEvent(
            eventId="event-" + uuid4().hex[:12],
            type="SemanticObjectRecorded",
            meetingId=meeting_id,
            sourceText=event.sourceText,
            field=event.field,
            value=(
                event.normalizedValue
                if event.normalizedValue is not None
                else event.value
            ),
            metadata={
                "domain": event.domain,
                "kind": event.kind,
                "relation": event.relation,
                "role": event.role,
                "actor": event.actor,
                "target": event.target,
                "status": event.status,
                "confidence": event.confidence,
                **event.metadata,
            },
        )

    @staticmethod
    def _dedupe(
        events: list[DecisionEvent],
    ) -> list[DecisionEvent]:

        seen = set()
        output = []

        for event in events:
            key = (
                event.type,
                event.field,
                str(event.value),
                event.sourceText,
                str(
                    event.metadata.get(
                        "domain",
                        "",
                    )
                ),
                str(
                    event.metadata.get(
                        "kind",
                        "",
                    )
                ),
                str(
                    event.metadata.get(
                        "role",
                        "",
                    )
                ),
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(event)

        return output


hybrid_event_extractor = HybridEventExtractor()