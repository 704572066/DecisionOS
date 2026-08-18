from fastapi import APIRouter, HTTPException

from app.intervention.delivery import active_intervention_delivery

router = APIRouter(prefix="/api/intervention-deliveries", tags=["intervention-delivery"])


@router.get("/{meeting_id}")
def list_deliveries(meeting_id: str):
    return {
        "deliveries": [
            item.model_dump(mode="json")
            for item in active_intervention_delivery.store.list(meeting_id)
        ],
        "diagnostics": active_intervention_delivery.diagnostics(meeting_id),
    }


@router.post("/{meeting_id}/{delivery_id}/acknowledge")
def acknowledge_delivery(meeting_id: str, delivery_id: str):
    record = active_intervention_delivery.acknowledge(meeting_id, delivery_id)
    if record is None:
        raise HTTPException(404, "Active intervention delivery not found or expired")
    return record.model_dump(mode="json")

