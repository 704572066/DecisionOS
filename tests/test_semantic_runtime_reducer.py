from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState
from app.runtime.state_reducer import runtime_state_reducer


def state():
    return RuntimeState(
        meetingId="m1",
        projectId="p1",
        contextId="c1",
    )


def semantic_event(*, domain, kind, field="", value=None, source=""):
    return DecisionEvent(
        eventId="e1",
        type="SemanticObjectRecorded",
        meetingId="m1",
        sourceText=source,
        field=field,
        value=value,
        metadata={
            "domain": domain,
            "kind": kind,
            "confidence": 0.95,
        },
    )


def test_delivery_constraint_enters_semantic_state():
    runtime = runtime_state_reducer.apply(
        state(),
        [semantic_event(
            domain="delivery",
            kind="constraint",
            field="deadline",
            value="2026-10-01",
            source="必须10月1日前上线",
        )],
    )
    item = runtime.decisionFacts["semanticState"]["delivery"][0]
    assert item["field"] == "deadline"
    assert item["value"] == "2026-10-01"


def test_replaceable_semantic_slot_keeps_latest_value():
    runtime = state()
    runtime_state_reducer.apply(runtime, [semantic_event(
        domain="resource",
        kind="resource_constraint",
        field="maxTeamSize",
        value=3,
        source="最多投入3个人",
    )])
    runtime_state_reducer.apply(runtime, [semantic_event(
        domain="resource",
        kind="resource_constraint",
        field="maxTeamSize",
        value=5,
        source="资源可以增加到5个人",
    )])
    items = runtime.decisionFacts["semanticState"]["resource"]
    assert len(items) == 1
    assert items[0]["value"] == 5


def test_commitments_accumulate_without_overwriting():
    runtime = state()
    runtime_state_reducer.apply(runtime, [semantic_event(
        domain="commitment",
        kind="commitment",
        value="推动内部审批",
        source="满足条件后我今天推动内部审批",
    )])
    runtime_state_reducer.apply(runtime, [semantic_event(
        domain="commitment",
        kind="commitment",
        value="本周完成技术确认",
        source="本周完成技术确认",
    )])
    items = runtime.decisionFacts["semanticState"]["commitment"]
    assert len(items) == 2
