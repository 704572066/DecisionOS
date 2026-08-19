from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select

from app.decision_board.service import decision_board_service
from app.models.entities import Meeting, MeetingDialogueTurn, MeetingFinalSnapshot, MeetingTranscriptSegment
from app.runtime.store import runtime_state_store


class MeetingFinalizationService:
    def end(self, db, meeting: Meeting) -> Meeting:
        if meeting.status == "finalized":
            return meeting
        if meeting.status == "ended":
            return meeting
        if meeting.status != "active":
            raise HTTPException(409, "Meeting cannot be ended from its current state")
        meeting.status = "ended"
        meeting.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(meeting)
        return meeting

    async def finalize(self, db, meeting: Meeting) -> MeetingFinalSnapshot:
        existing = db.scalar(select(MeetingFinalSnapshot).where(
            MeetingFinalSnapshot.workspace_id == meeting.workspace_id,
            MeetingFinalSnapshot.meeting_id == meeting.id,
        ))
        if existing:
            return existing
        if meeting.status != "ended":
            raise HTTPException(409, "Meeting must be ended before finalization")

        board = await decision_board_service.get(db, meeting)
        state = runtime_state_store.get(meeting.id)
        segments = list(db.scalars(select(MeetingTranscriptSegment).where(
            MeetingTranscriptSegment.workspace_id == meeting.workspace_id,
            MeetingTranscriptSegment.meeting_id == meeting.id,
        ).order_by(MeetingTranscriptSegment.sequence.asc())).all())
        dialogue = list(db.scalars(select(MeetingDialogueTurn).where(
            MeetingDialogueTurn.workspace_id == meeting.workspace_id,
            MeetingDialogueTurn.meeting_id == meeting.id,
        ).order_by(MeetingDialogueTurn.created_at.asc())).all())
        board_data = board.model_dump(mode="json")
        finalized_at = datetime.utcnow()
        payload = {
            "meeting": {
                "id": meeting.id,
                "title": meeting.title,
                "status": "finalized",
                "startedAt": meeting.created_at.isoformat(),
                "endedAt": meeting.ended_at.isoformat() if meeting.ended_at else None,
                "finalizedAt": finalized_at.isoformat(),
            },
            "objective": board.objective,
            "transcript": meeting.transcript or "",
            "segments": [{
                "id": row.id, "sequence": row.sequence, "speaker": row.speaker,
                "text": row.text, "confidence": row.confidence,
                "provider": row.asr_provider, "createdAt": row.created_at.isoformat(),
            } for row in segments],
            "canonicalContext": state.canonicalContext if state else "",
            "semanticState": dict((state.decisionFacts or {}).get("semanticState", {}) or {}) if state else {},
            "decisionState": dict(state.decisionState or {}) if state else {},
            "recentEvents": list(state.recentEvents or []) if state else [],
            "findings": board_data["reasoning"]["findings"],
            "recommendations": board_data["reasoning"]["recommendations"],
            "interventions": board_data["reasoning"]["interventions"],
            "dialogue": [{"role": row.role, "content": row.content, "createdAt": row.created_at.isoformat()} for row in dialogue],
            "evidence": board_data["evidence"],
            "decisionBoard": board_data,
        }
        snapshot = MeetingFinalSnapshot(
            workspace_id=meeting.workspace_id,
            meeting_id=meeting.id,
            version=1,
            payload=payload,
        )
        meeting.status = "finalized"
        meeting.finalized_at = finalized_at
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot


meeting_finalization_service = MeetingFinalizationService()

