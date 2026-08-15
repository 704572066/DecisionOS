from __future__ import annotations

from sqlalchemy.orm import Session

from app.decision_board.builder import (
    decision_board_builder,
)
from app.models.entities import Meeting
from app.reasoning import reasoning_service
from app.runtime.service import (
    runtime_state_service,
)


class DecisionBoardService:
    """
    DecisionBoard service with Reasoning as the only decision authority.

    Legacy DecisionBoardEngine is no longer used here.
    """

    async def get(
        self,
        db: Session,
        meeting: Meeting,
    ):
        state = (
            await runtime_state_service.get_or_refresh(
                db,
                meeting,
            )
        )

        reasoning = await reasoning_service.reason(
            state
        )

        return decision_board_builder.build(
            state=state,
            reasoning=reasoning,
        )

    async def refresh(
        self,
        db: Session,
        meeting: Meeting,
    ):
        state = (
            await runtime_state_service.refresh(
                db,
                meeting,
            )
        )

        reasoning = await reasoning_service.reason(
            state
        )

        return decision_board_builder.build(
            state=state,
            reasoning=reasoning,
        )


decision_board_service = (
    DecisionBoardService()
)
