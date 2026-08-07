from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.intelligence.reminder_engine import ai_reminder_engine
from app.models.entities import Meeting

router = APIRouter(prefix="/api/reminders", tags=["ai-reminder"])


@router.post("/meetings/{meeting_id}/generate")
async def generate_meeting_reminders(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return await ai_reminder_engine.generate(db, meeting)
