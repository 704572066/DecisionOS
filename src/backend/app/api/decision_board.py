from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.decision_board.service import decision_board_service
from app.models.entities import Meeting
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_meeting
router=APIRouter(prefix="/api/decision-board",tags=["decision-board"])
def meeting_or_404(db,workspace_id,meeting_id): return owned_meeting(db,workspace_id,meeting_id)
@router.get("/{meeting_id}")
async def get_board(meeting_id:str,db:Session=Depends(get_db),identity:CurrentIdentity=Depends(get_current_identity)):
    return (await decision_board_service.get(db,meeting_or_404(db,identity.workspace.id,meeting_id))).model_dump(mode="json")
@router.post("/{meeting_id}/refresh")
async def refresh_board(meeting_id:str,db:Session=Depends(get_db),identity:CurrentIdentity=Depends(get_current_identity)):
    return (await decision_board_service.refresh(db,meeting_or_404(db,identity.workspace.id,meeting_id))).model_dump(mode="json")
