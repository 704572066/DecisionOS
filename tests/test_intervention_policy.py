from datetime import datetime, timedelta, timezone

from types import SimpleNamespace

from app.intervention.policy import InterventionPolicy
from app.intervention.store import InterventionStore


def finding(
    *,
    fid: str,
    severity: str = "medium",
    confidence: float = 0.8,
    relevance: float = 0.8,
    urgency: str | None = None,
    status: str = "open",
):
    attrs = {
        "reasoningSource": "general",
        "decisionRelevance": relevance,
    }
    if urgency:
        attrs["urgency"] = urgency
    return SimpleNamespace(
        id=fid,
        type="risk",
        status=status,
        domain="general",
        subject=fid,
        title=fid,
        summary=f"summary:{fid}",
        severity=severity,
        confidence=confidence,
        sourceIds=[f"source:{fid}"],
        fingerprint=f"finding:{fid}",
        attributes=attrs,
    )


def recommendation(item):
    return SimpleNamespace(
        id=f"rec:{item.id}",
        meetingId="meeting-test",
        findingId=item.id,
        type="action",
        status="open",
        domain=item.domain,
        subject=item.subject,
        title=item.title,
        action=f"act:{item.id}",
        priority=item.severity,
        confidence=item.confidence,
        sourceIds=list(item.sourceIds),
        fingerprint=f"rec-fp:{item.id}",
        attributes={},
    )



state = SimpleNamespace(
    meetingId="meeting-test",
    projectId="project-test",
    contextId="context-test",
    diagnostics={},
    decisionState={},
)
store = InterventionStore()
policy = InterventionPolicy(store=store, cooldown_seconds=120)
now = datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc)

medium = finding(
    fid="medium-uncertainty",
    severity="medium",
    confidence=0.7,
    relevance=0.85,
)
high_low_urgency = finding(
    fid="high-low-urgency",
    severity="high",
    confidence=0.9,
    relevance=0.9,
    urgency="low",
)
high_imminent = finding(
    fid="high-imminent",
    severity="high",
    confidence=0.92,
    relevance=0.95,
    urgency="high",
)
low_conf = finding(
    fid="low-confidence",
    severity="high",
    confidence=0.55,
    relevance=0.95,
    urgency="high",
)
resolved = finding(
    fid="resolved",
    severity="critical",
    confidence=1.0,
    relevance=1.0,
    urgency="critical",
    status="resolved",
)
ordinary = finding(
    fid="ordinary",
    severity="low",
    confidence=0.6,
    relevance=0.3,
)

items = [
    medium,
    high_low_urgency,
    high_imminent,
    low_conf,
    resolved,
    ordinary,
]
recs = [recommendation(x) for x in items if x.status != "resolved"]

result = policy.evaluate(
    state=state,
    findings=items,
    recommendations=recs,
    now=now,
)
by_id = {x.findingId: x for x in result.decisions}

for key, item in by_id.items():
    print(key, item.level, item.reasonCode, item.score)

assert by_id["medium-uncertainty"].level == "surface"
assert by_id["high-low-urgency"].level == "surface"
assert by_id["high-imminent"].level == "interrupt"
assert by_id["low-confidence"].level == "surface"
assert by_id["low-confidence"].reasonCode == "interrupt_blocked_low_confidence"
assert by_id["resolved"].level == "silent"
assert by_id["resolved"].reasonCode == "inactive_finding"
assert by_id["ordinary"].level == "silent"

# Same interrupt-worthy Finding during cooldown must not interrupt twice.
second = policy.evaluate(
    state=state,
    findings=[high_imminent],
    recommendations=[recommendation(high_imminent)],
    now=now + timedelta(seconds=30),
)
repeat = second.decisions[0]
print("cooldown:", repeat.level, repeat.reasonCode)
assert repeat.level == "surface"
assert repeat.reasonCode == "interrupt_cooldown_active"

print("PHASE 2.3.1 INTERVENTION POLICY: OK")
