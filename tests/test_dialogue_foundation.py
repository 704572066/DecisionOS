from app.dialogue.models import (
    DialogueRequest,
    DialogueTurn,
)
from app.dialogue.store import DialogueStore


store = DialogueStore(
    max_turns=4
)

meeting_id = "meeting-test"

conversation_id_1 = (
    store.conversation_id(
        meeting_id
    )
)

store.append(
    meeting_id,
    DialogueTurn(
        role="user",
        content="刚才客户怎么说？",
    ),
)

store.append(
    meeting_id,
    DialogueTurn(
        role="assistant",
        content="客户只接受10%。",
    ),
)

conversation_id_2 = (
    store.conversation_id(
        meeting_id
    )
)

request = DialogueRequest(
    text="15%的方案呢？"
)

print(
    "conversation stable:",
    conversation_id_1
    == conversation_id_2
)

print(
    "history count:",
    len(
        store.list(
            meeting_id
        )
    )
)

print(
    "request:",
    request.model_dump(
        mode="json"
    )
)

store.clear(
    meeting_id
)

print(
    "history after reset:",
    len(
        store.list(
            meeting_id
        )
    )
)
