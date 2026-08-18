from fastapi import APIRouter, HTTPException, Depends

from app.intervention.delivery import active_intervention_delivery
from app.auth.dependencies import CurrentIdentity,get_current_identity
from app.auth.ownership import owned_meeting
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/intervention-deliveries", tags=["intervention-delivery"])


@router.get("/{meeting_id}")
def list_deliveries(meeting_id: str, db:Session=Depends(get_db), identity:CurrentIdentity=Depends(get_current_identity)):
    owned_meeting(db,identity.workspace.id,meeting_id)
    return {
        "deliveries": [
            item.model_dump(mode="json")
            for item in active_intervention_delivery.store.list(meeting_id,identity.workspace.id)
        ],
        "diagnostics": active_intervention_delivery.diagnostics(identity.workspace.id,meeting_id),
    }


@router.post("/{meeting_id}/{delivery_id}/acknowledge")
def acknowledge_delivery(meeting_id: str, delivery_id: str, db:Session=Depends(get_db), identity:CurrentIdentity=Depends(get_current_identity)):
    owned_meeting(db,identity.workspace.id,meeting_id)
    record = active_intervention_delivery.acknowledge(identity.workspace.id,meeting_id, delivery_id)
    if record is None:
        raise HTTPException(404, "Active intervention delivery not found or expired")
    return record.model_dump(mode="json")
