from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.context.service import build_meeting_context
from app.db.session import get_db
from app.models.entities import Meeting, Project
from app.retrieval.models import RetrievalQuery
from app.retrieval.query_builder import build_retrieval_query
from app.retrieval.service import hybrid_retriever
from app.retrieval.vector_store import coverage
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_meeting,owned_project

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])

class SearchBody(BaseModel):
    projectId: str
    text: str
    topics: list[str] = []
    facts: list[str] = []
    entities: list[str] = []
    topK: int = Field(default=8, ge=1, le=50)

@router.post("/search")
async def search(body: SearchBody, db: Session = Depends(get_db), identity: CurrentIdentity=Depends(get_current_identity)):
    owned_project(db,identity.workspace.id,body.projectId)
    query = RetrievalQuery(
        workspace_id=identity.workspace.id,
        project_id=body.projectId,
        text=body.text,
        topics=body.topics,
        facts=body.facts,
        entities=body.entities,
        top_k=body.topK,
    )
    return await hybrid_retriever.search(db, query)

@router.get("/meetings/{meeting_id}")
async def search_meeting(meeting_id: str, topK: int = 8, db: Session = Depends(get_db), identity: CurrentIdentity=Depends(get_current_identity)):
    meeting = owned_meeting(db,identity.workspace.id,meeting_id)
    context = build_meeting_context(db, meeting)
    result = await hybrid_retriever.search(
        db,
        build_retrieval_query(context, max(1, min(topK, 50))),
    )
    result["contextId"] = context.contextId
    result["cleanTranscriptWindow"] = context.cleanTranscriptWindow
    return result

@router.get("/coverage")
def get_coverage(projectId: str | None = None, db: Session = Depends(get_db), identity: CurrentIdentity=Depends(get_current_identity)):
    if projectId: owned_project(db,identity.workspace.id,projectId)
    return coverage(db, identity.workspace.id, projectId)
