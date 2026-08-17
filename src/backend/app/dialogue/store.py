from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from app.dialogue.models import DialogueTurn


class DialogueStore:
    """
    MVP in-memory dialogue history.

    Meeting-scoped because the current product dialogue is attached
    to one active meeting/session.

    Persistence can be introduced later without changing the
    ConversationAgent contract.
    """

    def __init__(
        self,
        *,
        max_turns: int = 20,
    ) -> None:
        self.max_turns = max_turns

        self._turns: dict[
            str,
            list[DialogueTurn],
        ] = defaultdict(list)

        self._conversation_ids: dict[
            str,
            str,
        ] = {}

    def conversation_id(
        self,
        meeting_id: str,
    ) -> str:

        current = self._conversation_ids.get(
            meeting_id
        )

        if current:
            return current

        current = (
            f"dialogue-{uuid4().hex[:12]}"
        )

        self._conversation_ids[
            meeting_id
        ] = current

        return current

    def list(
        self,
        meeting_id: str,
    ) -> list[DialogueTurn]:

        return list(
            self._turns.get(
                meeting_id,
                []
            )
        )

    def append(
        self,
        meeting_id: str,
        turn: DialogueTurn,
    ) -> None:

        turns = self._turns[
            meeting_id
        ]

        turns.append(
            turn
        )

        if len(turns) > self.max_turns:
            self._turns[
                meeting_id
            ] = turns[
                -self.max_turns:
            ]

    def clear(
        self,
        meeting_id: str,
    ) -> None:

        self._turns.pop(
            meeting_id,
            None,
        )

        self._conversation_ids.pop(
            meeting_id,
            None,
        )


dialogue_store = DialogueStore()
