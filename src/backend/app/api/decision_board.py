from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.decision_board.service import decision_board_service
from app.models.entities import Meeting
router=APIRouter(prefix="/api/decision-board",tags=["decision-board"])
def meeting_or_404(db,meeting_id):
    m=db.get(Meeting,meeting_id)
    if not m: raise HTTPException(404,"Meeting not found")
    return m
@router.get("/{meeting_id}")
async def get_board(meeting_id:str,db:Session=Depends(get_db)):
    return (await decision_board_service.get(db,meeting_or_404(db,meeting_id))).model_dump(mode="json")
@router.post("/{meeting_id}/refresh")
async def refresh_board(meeting_id:str,db:Session=Depends(get_db)):
    return (await decision_board_service.refresh(db,meeting_or_404(db,meeting_id))).model_dump(mode="json")
