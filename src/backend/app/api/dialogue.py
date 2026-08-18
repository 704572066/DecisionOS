from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dialogue import (
    DialogueRequest,
    dialogue_service,
)
from app.models.entities import Meeting
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_meeting


router = APIRouter(
    prefix="/api/dialogue",
    tags=["dialogue"],
)


def meeting_or_404(
    db: Session,
    workspace_id: str,
    meeting_id: str,
) -> Meeting:

    meeting = owned_meeting(db, workspace_id, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found",
        )

    return meeting


@router.post("/{meeting_id}")
async def ask_dialogue(
    meeting_id: str,
    request: DialogueRequest,
    db: Session = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
):
    meeting = meeting_or_404(
        db,
        identity.workspace.id,
        meeting_id,
    )

    try:
        response = (
            await dialogue_service.ask(
                db,
                meeting,
                request,
            )
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    return response.model_dump(
        mode="json"
    )


@router.delete("/{meeting_id}")
async def reset_dialogue(
    meeting_id: str,
    db: Session = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
):
    meeting = meeting_or_404(
        db,
        identity.workspace.id,
        meeting_id,
    )

    dialogue_service.reset(
        meeting
    )

    return {
        "meetingId": meeting.id,
        "reset": True,
    }
