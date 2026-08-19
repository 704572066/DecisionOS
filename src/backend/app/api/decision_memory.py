from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.ownership import owned_meeting
from app.db.session import get_db
from app.meetings.decision_memory import decision_memory_service

router = APIRouter(prefix="/api/decision-memories", tags=["decision-memory"])


def memory_json(row):
    return {
        "id": row.id, "workspaceId": row.workspace_id, "sourceMeetingId": row.source_meeting_id,
        "sourceSummaryId": row.source_summary_id, "sourceDecisionId": row.source_decision_id,
        "supersedesId": row.supersedes_id, "type": "decision", "title": row.title,
        "decision": row.decision, "subject": row.subject, "status": row.status,
        "confidence": row.confidence, "sourceIds": row.source_ids, "evidence": row.evidence,
        "effectiveAt": row.effective_at.isoformat(), "createdAt": row.created_at.isoformat(),
        "attributes": row.attributes,
    }


@router.get("")
def list_memories(response: Response, meetingId: str | None = None, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    response.headers["Cache-Control"] = "private, no-store"
    if meetingId:
        owned_meeting(db, identity.workspace.id, meetingId)
    return [memory_json(row) for row in decision_memory_service.list(db, identity.workspace.id, meetingId)]


@router.post("/{memory_id}/revoke")
def revoke_memory(memory_id: str, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    row = decision_memory_service.revoke(db, identity.workspace.id, memory_id)
    if not row:
        raise HTTPException(404, "Decision memory not found")
    return memory_json(row)

