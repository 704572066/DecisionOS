from sqlalchemy.orm import Session
from app.decision_board.engine import decision_board_engine
from app.models.entities import Meeting
from app.runtime.service import runtime_state_service
class DecisionBoardService:
    async def get(self,db:Session,meeting:Meeting): return decision_board_engine.build(await runtime_state_service.get_or_refresh(db,meeting))
    async def refresh(self,db:Session,meeting:Meeting): return decision_board_engine.build(await runtime_state_service.refresh(db,meeting))
decision_board_service=DecisionBoardService()
