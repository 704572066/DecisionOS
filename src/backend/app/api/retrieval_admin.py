from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.retrieval.indexer import backfill_embeddings
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_project

router = APIRouter(prefix="/api/retrieval/admin", tags=["retrieval-admin"])

class BackfillBody(BaseModel):
    projectId: str | None = None
    batchSize: int = Field(default=16, ge=1, le=100)
    force: bool = False

@router.post("/backfill")
async def backfill(body: BackfillBody, db: Session = Depends(get_db), identity:CurrentIdentity=Depends(get_current_identity)):
    if body.projectId: owned_project(db,identity.workspace.id,body.projectId)
    return await backfill_embeddings(db, identity.workspace.id, body.projectId, body.batchSize, body.force)
