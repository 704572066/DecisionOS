import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.decision.candidate_service import decision_candidate_service
from app.decision.models import CandidateFromReminderRequest, ConfirmDecisionRequest
from app.models.entities import Decision, KnowledgeItem, Meeting, Task
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_meeting,owned_project

router=APIRouter(prefix="/api/decisions", tags=["decision-loop"])

@router.post("/meetings/{meeting_id}/candidate")
async def create_candidate(meeting_id: str, body: CandidateFromReminderRequest, db: Session=Depends(get_db), identity:CurrentIdentity=Depends(get_current_identity)):
    meeting=owned_meeting(db,identity.workspace.id,meeting_id)
    candidate=await decision_candidate_service.from_reminder(db, meeting, body.reminder)
    return candidate.model_dump(mode="json")

@router.post("/confirm")
def confirm_candidate(body: ConfirmDecisionRequest, db: Session=Depends(get_db), identity:CurrentIdentity=Depends(get_current_identity)):
    candidate=body.candidate
    meeting=owned_meeting(db,identity.workspace.id,candidate.meetingId)
    owned_project(db,identity.workspace.id,candidate.projectId)
    if meeting.project_id != candidate.projectId: raise HTTPException(400,"Candidate project/meeting mismatch")
    title=(body.title or candidate.title).strip(); statement=(body.statement or candidate.statement).strip()
    if not title or not statement: raise HTTPException(400,"Decision title and statement are required")
    evidence_summary=json.dumps({
        "candidateId":candidate.candidateId,
        "contextId":candidate.contextId,
        "reasons":candidate.reasons,
        "risks":candidate.risks,
        "evidence":[x.model_dump(mode="json") for x in candidate.evidence],
    }, ensure_ascii=False)
    decision=Decision(workspace_id=identity.workspace.id,project_id=candidate.projectId, meeting_id=candidate.meetingId, title=title, statement=statement, evidence_summary=evidence_summary)
    db.add(decision); db.flush()
    db.add(KnowledgeItem(workspace_id=identity.workspace.id,project_id=None, object_type="decision", title=title, content=statement, source_type="decision", source_id=decision.id))
    task=None
    if body.taskTitle and body.taskObjective:
        task=Task(workspace_id=identity.workspace.id,project_id=candidate.projectId, decision_id=decision.id, title=body.taskTitle.strip(), objective=body.taskObjective.strip(), owner=body.taskOwner.strip())
        db.add(task)
    db.commit(); db.refresh(decision)
    return {"decisionId":decision.id,"taskId":task.id if task else None,"status":"confirmed","knowledgeUpdated":True}

