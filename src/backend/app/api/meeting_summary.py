from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.ownership import owned_meeting
from app.db.session import get_db
from app.meetings.summary_service import meeting_summary_service

router = APIRouter(prefix="/api/meeting-history", tags=["meeting-summary"])


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


@router.get("/{meeting_id}/summary")
def get_summary(meeting_id: str, response: Response, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    no_store(response)
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    row = meeting_summary_service.get(db, meeting)
    if not row:
        raise HTTPException(404, "Meeting summary not generated")
    return meeting_summary_service.result(row).model_dump(mode="json")


@router.post("/{meeting_id}/summary")
async def generate_summary(meeting_id: str, response: Response, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    no_store(response)
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    if meeting.status != "finalized":
        raise HTTPException(409, "Meeting must be finalized before summary generation")
    try:
        row = await meeting_summary_service.generate(db, meeting)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return meeting_summary_service.result(row).model_dump(mode="json")

