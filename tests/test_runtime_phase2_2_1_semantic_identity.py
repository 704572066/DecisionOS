from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState
from app.runtime.state_reducer import RuntimeStateReducer


def _event(event_id, text, value, actor, role, status):
    return DecisionEvent(
        eventId=event_id,
        type="SemanticObjectRecorded",
        meetingId="meeting-test",
        sourceText=text,
        field="discountPercent",
        value=value,
        metadata={
            "domain": "commercial",
            "kind": "fact_change",
            "actor": actor,
            "role": role,
            "status": status,
            "confidence": 0.95,
        },
    )


def test_semantic_identity_includes_actor_and_role():
    state = RuntimeState(
        meetingId="meeting-test",
        projectId="project-test",
        contextId="context-test",
    )
    reducer = RuntimeStateReducer()

    state = reducer.apply(state, [
        _event("e18", "客户要求整体价格下降18%", 18, "customer", "requirement", "proposed"),
        _event("e8", "按8%折扣推进", 8, "us", "commitment", "confirmed"),
        _event("e15", "改为15%折扣推进", 15, "us", "commitment", "confirmed"),
        _event("e15r", "客户不同意15%", 15, "us", "commitment", "rejected"),
        _event("e10", "只接受10%", 10, "customer", "requirement", "confirmed"),
    ])

    items = state.decisionFacts["semanticState"]["commercial"]
    positions = {(item["actor"], item["role"]): item for item in items}

    assert len(items) == 2
    assert positions[("customer", "requirement")]["value"] == 10
    assert positions[("customer", "requirement")]["status"] == "confirmed"
    assert positions[("us", "commitment")]["value"] == 15
    assert positions[("us", "commitment")]["status"] == "rejected"
