from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Decision, KnowledgeItem, Meeting, Project, Task
from app.schemas.contracts import DecisionCreate, MeetingCreate, ProjectCreate, TranscriptAppend
from app.services.context_service import analyze_meeting

router = APIRouter(prefix="/api")

@router.post("/demo/seed")
def seed_demo(db: Session = Depends(get_db)):
    project = db.scalar(select(Project).where(Project.name == "客户A企业软件采购项目"))
    if not project:
        project = Project(name="客户A企业软件采购项目", business_goal="在保证利润率的前提下完成签约")
        db.add(project); db.flush()
        rows = [
            ("document", "历史同类客户成交复盘", "去年同类型客户初始要求降价20%，最终成交折扣为8%。", "document"),
            ("evidence", "客户A历史付款记录", "客户A过去合同平均付款周期为90天，曾出现一次逾期。", "crm"),
            ("evidence", "公司项目利润率规则", "软件项目目标毛利率不得低于18%；超过10%的折扣必须评估付款周期。", "policy"),
        ]
        for typ, title, content, source in rows:
            db.add(KnowledgeItem(project_id=project.id, object_type=typ, title=title, content=content, source_type=source))
        db.commit(); db.refresh(project)
    return {"projectId": project.id, "message": "示例知识已导入"}

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "businessGoal": p.business_goal} for p in db.scalars(select(Project)).all()]

@router.post("/projects")
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    p = Project(name=body.name, business_goal=body.businessGoal); db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "name": p.name}

@router.post("/meetings")
def create_meeting(body: MeetingCreate, db: Session = Depends(get_db)):
    if not db.get(Project, body.projectId): raise HTTPException(404, "Project not found")
    m = Meeting(project_id=body.projectId, title=body.title); db.add(m); db.commit(); db.refresh(m)
    return {"id": m.id, "projectId": m.project_id, "title": m.title, "transcript": m.transcript}

@router.post("/meetings/{meeting_id}/transcript")
def append_transcript(meeting_id: str, body: TranscriptAppend, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m: raise HTTPException(404, "Meeting not found")
    m.transcript = (m.transcript + "\n" + body.text).strip(); db.commit()
    return {"id": m.id, "transcript": m.transcript}

@router.post("/meetings/{meeting_id}/analyze")
def analyze(meeting_id: str, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m: raise HTTPException(404, "Meeting not found")
    return analyze_meeting(db, m)

@router.post("/decisions")
def create_decision(body: DecisionCreate, db: Session = Depends(get_db)):
    d = Decision(project_id=body.projectId, meeting_id=body.meetingId, title=body.title, statement=body.statement, evidence_summary=body.evidenceSummary)
    db.add(d); db.flush()
    db.add(KnowledgeItem(project_id=body.projectId, object_type="decision", title=body.title, content=body.statement, source_type="decision", source_id=d.id))
    task = None
    if body.taskTitle and body.taskObjective:
        task = Task(project_id=body.projectId, decision_id=d.id, title=body.taskTitle, objective=body.taskObjective, owner=body.taskOwner)
        db.add(task)
    db.commit(); db.refresh(d)
    return {"decisionId": d.id, "taskId": task.id if task else None}
