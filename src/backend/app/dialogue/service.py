from __future__ import annotations

from sqlalchemy.orm import Session

from app.dialogue.agent import (
    ConversationAgent,
    conversation_agent,
)
from app.dialogue.models import (
    DialogueRequest,
    DialogueResponse,
    DialogueTurn,
)
from app.dialogue.store import (
    DialogueStore,
    dialogue_store,
)
from app.models.entities import Meeting, MeetingDialogueTurn
from app.reasoning import reasoning_service
from app.runtime.service import (
    runtime_state_service,
)


class DialogueService:
    """
    Meeting-aware direct dialogue service.

    Dialogue and DecisionBoard share Runtime/Reasoning state but are
    independent interaction surfaces.
    """

    def __init__(
        self,
        *,
        agent: ConversationAgent | None = None,
        store: DialogueStore | None = None,
    ) -> None:

        self.agent = (
            agent
            if agent is not None
            else conversation_agent
        )

        self.store = (
            store
            if store is not None
            else dialogue_store
        )

    async def ask(
        self,
        db: Session,
        meeting: Meeting,
        request: DialogueRequest,
    ) -> DialogueResponse:

        state = (
            await runtime_state_service.get_or_refresh(
                db,
                meeting,
            )
        )

        reasoning = await reasoning_service.get_or_reason(
            state
        )

        history = self.store.list(
            meeting.id, meeting.workspace_id
        )

        conversation_id = (
            self.store.conversation_id(
                meeting.id
                , meeting.workspace_id
            )
        )

        response = await self.agent.answer(
            meeting_id=meeting.id,
            conversation_id=conversation_id,
            question=request.text,
            state=state,
            reasoning=reasoning,
            history=history,
        )

        self.store.append(
            meeting.id,
            DialogueTurn(
                role="user",
                content=request.text,
            ), meeting.workspace_id,
        )

        self.store.append(
            meeting.id,
            DialogueTurn(
                role="assistant",
                content=response.answer,
            ), meeting.workspace_id,
        )

        db.add_all([
            MeetingDialogueTurn(
                workspace_id=meeting.workspace_id,
                meeting_id=meeting.id,
                role="user",
                content=request.text,
            ),
            MeetingDialogueTurn(
                workspace_id=meeting.workspace_id,
                meeting_id=meeting.id,
                role="assistant",
                content=response.answer,
            ),
        ])
        db.commit()

        return response

    def reset(
        self,
        meeting: Meeting,
    ) -> None:

        self.store.clear(
            meeting.id, meeting.workspace_id
        )


dialogue_service = DialogueService()

