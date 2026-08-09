from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.reminder_engine import ai_reminder_engine
from app.models.entities import Meeting, MeetingTranscriptSegment
from app.runtime.event_extractor import event_extractor
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
            decisionFacts=dict(previous.decisionFacts) if previous else {},
            recentEvents=list(previous.recentEvents) if previous else [],
            resolvedRiskKeys=list(previous.resolvedRiskKeys) if previous else [],
            diagnostics={
                "reminder": result.get("diagnostics") or {},
                "retrieval": retrieval.get("diagnostics") or {},
            },
        )

        latest_text = self._latest_final_segment_text(db, meeting.id)
        if not latest_text:
            latest_text = state.canonicalContext

        events = event_extractor.extract(
            meeting.id,
            latest_text,
            previous,
        )
        state = runtime_state_reducer.apply(state, events)
        state.diagnostics["eventsExtracted"] = len(events)

        return runtime_state_store.put(state)

    async def get_or_refresh(
        self,
        db: Session,
        meeting: Meeting,
    ) -> RuntimeState:
        cached = runtime_state_store.get(meeting.id)
        if cached is not None:
            return cached
        return await self.refresh(db, meeting)

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
    def _latest_final_segment_text(
        db: Session,
        meeting_id: str,
    ) -> str:
        stmt = (
            select(MeetingTranscriptSegment)
            .where(
                MeetingTranscriptSegment.meeting_id == meeting_id,
                MeetingTranscriptSegment.is_final.is_(True),
            )
            .order_by(MeetingTranscriptSegment.sequence.desc())
            .limit(1)
        )
        segment = db.scalar(stmt)
        return segment.text.strip() if segment else ""


runtime_state_service = RuntimeStateService()
