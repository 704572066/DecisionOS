from sqlalchemy.orm import Session
from app.decision_board.engine import decision_board_engine
from app.models.entities import Meeting
from app.runtime.service import runtime_state_service
from app.reasoning import reasoning_service
from app.decision_board.models import (
    DecisionBoardReasoning
)

class DecisionBoardService:

    async def get(
        self,
        db: Session,
        meeting: Meeting
    ):

        state = await runtime_state_service.get_or_refresh(
            db,
            meeting
        )

        board = decision_board_engine.build(
            state
        )

        reasoning = await reasoning_service.reason(
            state
        )

        board.reasoning = DecisionBoardReasoning(
            findings=reasoning.findings,
            constraints=reasoning.constraints,
            diagnostics=(
                reasoning.diagnostics.model_dump(
                    mode="json"
                )
                if hasattr(
                    reasoning.diagnostics,
                    "model_dump"
                )
                else reasoning.diagnostics
            ),
        )

        return board

    async def refresh(
    self,
    db: Session,
    meeting: Meeting
    ):

        state = await runtime_state_service.refresh(
            db,
            meeting
        )

        board = decision_board_engine.build(
            state
        )

        reasoning = await reasoning_service.reason(
            state
        )

        board.reasoning = DecisionBoardReasoning(
            findings=reasoning.findings,
            constraints=reasoning.constraints,
            diagnostics=(
                reasoning.diagnostics.model_dump(
                    mode="json"
                )
                if hasattr(
                    reasoning.diagnostics,
                    "model_dump"
                )
                else reasoning.diagnostics
            ),
        )

        return board

decision_board_service=DecisionBoardService()
