from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.ownership import owned_meeting
from app.db.session import get_db
from app.meetings.finalization import meeting_finalization_service
from app.models.entities import Meeting, MeetingFinalSnapshot

router = APIRouter(prefix="/api/meeting-history", tags=["meeting-history"])


def disable_private_cache(response: Response) -> None:
    # History snapshots contain workspace-private meeting content. Explicitly
    # prevent a browser from reusing one user's response after account switch.
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"


def meeting_json(meeting: Meeting):
    return {
        "id": meeting.id, "title": meeting.title, "status": meeting.status,
        "startedAt": meeting.created_at.isoformat(),
        "endedAt": meeting.ended_at.isoformat() if meeting.ended_at else None,
        "finalizedAt": meeting.finalized_at.isoformat() if meeting.finalized_at else None,
    }


@router.get("")
def list_history(response: Response, db: Session = Depends(get_db),
                 identity: CurrentIdentity = Depends(get_current_identity)):
    disable_private_cache(response)
    meetings = db.scalars(select(Meeting).where(
        Meeting.workspace_id == identity.workspace.id,
        Meeting.status.in_(["ended", "finalized"]),
    ).order_by(Meeting.created_at.desc())).all()
    return [meeting_json(meeting) for meeting in meetings]


@router.get("/{meeting_id}")
def get_history(meeting_id: str, response: Response, db: Session = Depends(get_db),
                identity: CurrentIdentity = Depends(get_current_identity)):
    disable_private_cache(response)
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    if meeting.status == "active":
        raise HTTPException(409, "Meeting is still active")
    snapshot = db.scalar(select(MeetingFinalSnapshot).where(
        MeetingFinalSnapshot.workspace_id == identity.workspace.id,
        MeetingFinalSnapshot.meeting_id == meeting.id,
    ))
    return {"meeting": meeting_json(meeting), "snapshot": snapshot.payload if snapshot else None}


@router.post("/{meeting_id}/end")
def end_meeting(meeting_id: str, db: Session = Depends(get_db),
                identity: CurrentIdentity = Depends(get_current_identity)):
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    return meeting_json(meeting_finalization_service.end(db, meeting))


@router.post("/{meeting_id}/finalize")
async def finalize_meeting(meeting_id: str, db: Session = Depends(get_db),
                           identity: CurrentIdentity = Depends(get_current_identity)):
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    snapshot = await meeting_finalization_service.finalize(db, meeting)
    return {"snapshotId": snapshot.id, "version": snapshot.version, "snapshot": snapshot.payload}

