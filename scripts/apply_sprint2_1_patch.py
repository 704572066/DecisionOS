#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rep(p,o,n):
 t=p.read_text(encoding='utf-8')
 if n in t:return print('already',p)
 if o not in t:raise SystemExit(f'expected text not found in {p}: {o}')
 p.write_text(t.replace(o,n,1),encoding='utf-8'); print('patched',p)
r=R/'src/backend/app/api/routes.py'
rep(r,'from app.db.session import get_db\n','from app.context.builder import context_builder\nfrom app.context.service import build_meeting_context\nfrom app.db.session import get_db\n')
rep(r,'from app.schemas.contracts import DecisionCreate, MeetingCreate, ProjectCreate, TranscriptAppend\n','from app.schemas.contracts import ContextBuildRequest, DecisionCreate, MeetingCreate, ProjectCreate, TranscriptAppend\n')
marker='@router.post("/decisions")\ndef create_decision'
insert="""@router.get("/meetings/{meeting_id}/context")
def get_meeting_context(meeting_id: str, maxCharacters: int = 1600, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return build_meeting_context(db, meeting, max_characters=max(200, min(maxCharacters, 12000))).model_dump(mode="json")

@router.post("/context/build")
def build_context(body: ContextBuildRequest, db: Session = Depends(get_db)):
    project = db.get(Project, body.projectId)
    if not project:
        raise HTTPException(404, "Project not found")
    transcript = body.transcript
    if body.meetingId:
        meeting = db.get(Meeting, body.meetingId)
        if not meeting:
            raise HTTPException(404, "Meeting not found")
        if meeting.project_id != body.projectId:
            raise HTTPException(400, "Meeting does not belong to project")
        if not transcript:
            transcript = meeting.transcript or ""
    return context_builder.build(db, project_id=body.projectId, meeting_id=body.meetingId, transcript=transcript, objective=body.objective, max_characters=body.maxCharacters).model_dump(mode="json")

@router.post("/decisions")
def create_decision"""
rep(r,marker,insert)
rem=R/'src/backend/app/services/reminder_service.py'
rep(rem,'                "reminders": deduplicated,\n','                "reminders": deduplicated,\n                "context": result.get("context"),\n')
a=R/'src/backend/app/api/audio_ws.py'
rep(a,'                    "reminders": result["reminders"],\n','                    "reminders": result["reminders"],\n                    "context": result.get("context"),\n')
print('Sprint 2-1 backend integration complete')
