from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.intelligence.reminder_engine import ai_reminder_engine
from app.models.entities import Meeting, MeetingTranscriptSegment
from app.runtime.event_extractor import event_extractor
from app.runtime.hybrid_event_extractor import hybrid_event_extractor
from app.runtime.models import RuntimeState
from app.runtime.state_reducer import runtime_state_reducer
from app.runtime.store import runtime_state_store


class RuntimeStateService:
    async def refresh(
        self,
        db: Session,
        meeting: Meeting,
    ) -> RuntimeState:
        previous = runtime_state_store.get(meeting.id)

        result = await ai_reminder_engine.generate(db, meeting)
        context = result["context"]
        retrieval = result["retrieval"]

        state = RuntimeState(
            meetingId=meeting.id,
            projectId=meeting.project_id,
            contextId=context["contextId"],
            objective=context.get("currentObjective", ""),
            canonicalContext=context.get("cleanTranscriptWindow", ""),
            topics=list(context.get("topics") or []),
            facts=list(context.get("facts") or []),
            constraints=list(context.get("constraints") or []),
            retrievalMode=retrieval.get("mode", "keyword"),
            retrievalResults=list(retrieval.get("results") or []),
            rerankedEvidence=list(result.get("rerankedEvidence") or []),
            reminders=list(result.get("reminders") or []),
            decisionFacts=(
                dict(previous.decisionFacts)
                if previous
                else self._decision_facts_from_context(context)
            ),
            decisionState=(dict(previous.decisionState) if previous else {}),
            recentEvents=list(previous.recentEvents) if previous else [],
            resolvedRiskKeys=list(previous.resolvedRiskKeys) if previous else [],
            diagnostics={
                "reminder": result.get("diagnostics") or {},
                "retrieval": retrieval.get("diagnostics") or {},
            },
        )

        # Phase 2.2: build state by replaying every final transcript segment
        # in sequence. Processing only the latest segment loses intermediate
        # proposals/rejections and leaves semanticState stale.
        pending_segments = self._final_segments_after(
            db, meeting.id, 0
        )
        extracted_count = 0
        for segment in pending_segments:
            text = (segment.text or "").strip()
            if not text:
                continue
            events = await hybrid_event_extractor.extract(
                meeting.id,
                text,
                state,
                semantic_enabled=bool(
                    getattr(settings, "semantic_event_enabled", True)
                ),
                meeting_date=meeting.created_at,
            )
            state = runtime_state_reducer.apply(state, events)
            state.lastProcessedSegmentSequence = segment.sequence
            extracted_count += len(events)

        # Backward-compatible fallback for meetings without persisted segments.
        if not pending_segments and state.canonicalContext:
            events = await hybrid_event_extractor.extract(
                meeting.id,
                state.canonicalContext,
                state,
                semantic_enabled=bool(
                    getattr(settings, "semantic_event_enabled", True)
                ),
                meeting_date=meeting.created_at,
            )
            state = runtime_state_reducer.apply(state, events)
            extracted_count += len(events)

        state.diagnostics["eventsExtracted"] = extracted_count

        return runtime_state_store.put(state)

    async def get_or_refresh(
        self,
        db: Session,
        meeting: Meeting,
    ) -> RuntimeState:
        cached = runtime_state_store.get(meeting.id)

        if cached is None:
            return await self.refresh(db, meeting)

        pending_segments = self._final_segments_after(
            db,
            meeting.id,
            cached.lastProcessedSegmentSequence,
        )
        if not pending_segments:
            return cached

        updated = cached
        extracted_count = 0
        for segment in pending_segments:
            events = await hybrid_event_extractor.extract(
                meeting.id,
                (segment.text or "").strip(),
                updated,
                semantic_enabled=bool(
                    getattr(settings, "semantic_event_enabled", True)
                ),
                meeting_date=meeting.created_at,
            )
            updated = runtime_state_reducer.apply(updated, events)
            updated.lastProcessedSegmentSequence = segment.sequence
            extracted_count += len(events)

        updated.diagnostics["eventsExtractedSemantic"] = extracted_count
        return runtime_state_store.put(updated)

    async def apply_semantic_transcript_event(
        self,
        meeting: Meeting,
        text: str,
    ) -> RuntimeState | None:
        """Apply hybrid rule + semantic events for a new final segment."""
        state = runtime_state_store.get(meeting.id)
        if state is None:
            return None

        events = await hybrid_event_extractor.extract(
            meeting.id,
            text,
            state,
            semantic_enabled=bool(
                getattr(settings, "semantic_event_enabled", True)
            ),
            meeting_date=meeting.created_at,
        )
        if not events:
            return state

        runtime_state_reducer.apply(state, events)
        state.diagnostics["eventsExtractedSemantic"] = len(events)
        return runtime_state_store.put(state)

    def apply_transcript_event(
        self,
        meeting: Meeting,
        text: str,
    ) -> RuntimeState | None:
        """Lightweight real-time update; never calls Retriever or LLM."""
        state = runtime_state_store.get(meeting.id)
        if state is None:
            return None

        events = event_extractor.extract(
            meeting.id,
            text,
            state,
        )
        if not events:
            return state

        runtime_state_reducer.apply(state, events)
        state.diagnostics["eventsExtractedRealtime"] = len(events)
        return runtime_state_store.put(state)

    @staticmethod
    def _decision_facts_from_context(context: dict) -> dict:
        output: dict = {}
        canonical = (
            context.get("cleanTranscriptWindow")
            or context.get("transcriptWindow")
            or ""
        )

        for fact in context.get("facts") or []:
            fact_type = fact.get("factType") or ""
            value = fact.get("normalizedValue") or fact.get("text") or ""

            if (
                fact_type == "percentage"
                and any(
                    term in canonical
                    for term in ("降价", "折扣", "优惠", "价格下降", "价格下调")
                )
            ):
                match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(value))
                if match:
                    output["discountPercent"] = float(match.group(1))

            if (
                fact_type == "duration"
                and any(
                    term in canonical
                    for term in ("付款", "账期", "回款")
                )
            ):
                match = re.search(r"(\d+)\s*天", str(value))
                if match:
                    output["paymentTermDays"] = int(match.group(1))

        return output


    @staticmethod
    def _final_segments_after(
        db: Session,
        meeting_id: str,
        after_sequence: int,
    ) -> list[MeetingTranscriptSegment]:
        stmt = (
            select(MeetingTranscriptSegment)
            .where(
                MeetingTranscriptSegment.meeting_id == meeting_id,
                MeetingTranscriptSegment.is_final.is_(True),
                MeetingTranscriptSegment.sequence > after_sequence,
            )
            .order_by(MeetingTranscriptSegment.sequence.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def _latest_final_segment(
        db: Session,
        meeting_id: str,
    ) -> MeetingTranscriptSegment | None:
        stmt = (
            select(MeetingTranscriptSegment)
            .where(
                MeetingTranscriptSegment.meeting_id == meeting_id,
                MeetingTranscriptSegment.is_final.is_(True),
            )
            .order_by(
                MeetingTranscriptSegment.sequence.desc()
            )
            .limit(1)
        )

        return db.scalar(stmt)

runtime_state_service = RuntimeStateService()
