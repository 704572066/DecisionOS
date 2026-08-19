from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.builder import context_builder
from app.context.service import build_meeting_context
from app.db.session import get_db
from app.models.entities import Decision, KnowledgeItem, Meeting, Project, Task
from app.schemas.contracts import ContextBuildRequest, DecisionCreate, MeetingCreate, ProjectCreate, TranscriptAppend
from app.services.context_service import analyze_meeting
from app.services.transcript_service import append_final_segment, list_segments
from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.ownership import owned_meeting, owned_project
from app.workspace.defaults import ensure_default_project

router = APIRouter(prefix="/api")


@router.get("/projects")
def list_projects(db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    return [
        {"id": p.id, "name": p.name, "businessGoal": p.business_goal}
        for p in db.scalars(select(Project).where(Project.workspace_id == identity.workspace.id)).all()
    ]


@router.post("/projects")
def create_project(body: ProjectCreate, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    p = Project(workspace_id=identity.workspace.id, name=body.name, business_goal=body.businessGoal)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}


@router.post("/meetings")
def create_meeting(body: MeetingCreate, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    project = owned_project(db, identity.workspace.id, body.projectId) if body.projectId else ensure_default_project(db, identity.workspace.id)
    m = Meeting(workspace_id=identity.workspace.id, project_id=project.id, title=body.title)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "projectId": m.project_id, "title": m.title, "transcript": m.transcript}


@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    m = owned_meeting(db, identity.workspace.id, meeting_id)
    segments = list_segments(db, meeting_id, workspace_id=identity.workspace.id)
    return {
        "id": m.id,
        "projectId": m.project_id,
        "title": m.title,
        "status": m.status,
        "transcript": m.transcript,
        "segments": [
            {
                "id": segment.id,
                "sequence": segment.sequence,
                "speaker": segment.speaker,
                "text": segment.text,
                "confidence": segment.confidence,
                "provider": segment.asr_provider,
                "createdAt": segment.created_at.isoformat(),
            }
            for segment in segments
        ],
    }


@router.post("/meetings/{meeting_id}/transcript")
def append_transcript(meeting_id: str, body: TranscriptAppend, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    m = owned_meeting(db, identity.workspace.id, meeting_id)
    # segment = append_final_segment(db, meeting=m, text=body.text, provider="manual")
    # return {"id": m.id, "transcript": m.transcript, "segmentId": segment.id}
    result = append_final_segment(
        db,
        meeting=m,
        text=body.text,
        provider="manual"
    )

    return {
        "id": m.id,
        "transcript": m.transcript,
        "segmentId": result.segment.id,
        "created": result.created,
        "replacedSegmentId": result.replaced_segment_id,
    }


@router.post("/meetings/{meeting_id}/analyze")
def analyze(meeting_id: str, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    m = owned_meeting(db, identity.workspace.id, meeting_id)
    return analyze_meeting(db, m)


@router.get("/meetings/{meeting_id}/context")
def get_meeting_context(meeting_id: str, maxCharacters: int = 1600, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    meeting = owned_meeting(db, identity.workspace.id, meeting_id)
    return build_meeting_context(db, meeting, max_characters=max(200, min(maxCharacters, 12000))).model_dump(mode="json")

@router.post("/context/build")
def build_context(body: ContextBuildRequest, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    project = owned_project(db, identity.workspace.id, body.projectId)
    transcript = body.transcript
    if body.meetingId:
        meeting = owned_meeting(db, identity.workspace.id, body.meetingId)
        if meeting.project_id != body.projectId:
            raise HTTPException(400, "Meeting does not belong to project")
        if not transcript:
            transcript = meeting.transcript or ""
    return context_builder.build(db, workspace_id=identity.workspace.id, project_id=body.projectId, meeting_id=body.meetingId, transcript=transcript, objective=body.objective, max_characters=body.maxCharacters).model_dump(mode="json")

@router.post("/decisions")
def create_decision(body: DecisionCreate, db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    owned_project(db, identity.workspace.id, body.projectId)
    if body.meetingId:
        meeting = owned_meeting(db, identity.workspace.id, body.meetingId)
        if meeting.project_id != body.projectId: raise HTTPException(400, "Meeting does not belong to project")
    d = Decision(
        workspace_id=identity.workspace.id,
        project_id=body.projectId,
        meeting_id=body.meetingId,
        title=body.title,
        statement=body.statement,
        evidence_summary=body.evidenceSummary,
    )
    db.add(d)
    db.flush()
    db.add(
        KnowledgeItem(
            workspace_id=identity.workspace.id,
            project_id=None,
            object_type="decision",
            title=body.title,
            content=body.statement,
            source_type="decision",
            source_id=d.id,
        )
    )
    task = None
    if body.taskTitle and body.taskObjective:
        task = Task(
            workspace_id=identity.workspace.id,
            project_id=body.projectId,
            decision_id=d.id,
            title=body.taskTitle,
            objective=body.taskObjective,
            owner=body.taskOwner,
        )
        db.add(task)
    db.commit()
    db.refresh(d)
    return {"decisionId": d.id, "taskId": task.id if task else None}

