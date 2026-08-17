from app.runtime.models import RuntimeState


def test_runtime_state_cursor_can_be_preserved_across_rebuild():
    previous = RuntimeState(
        meetingId="meeting-test",
        projectId="project-test",
        contextId="context-old",
        lastProcessedSegmentSequence=4,
    )

    rebuilt = RuntimeState(
        meetingId=previous.meetingId,
        projectId=previous.projectId,
        contextId="context-new",
        decisionFacts=dict(previous.decisionFacts),
        decisionState=dict(previous.decisionState),
        recentEvents=list(previous.recentEvents),
        resolvedRiskKeys=list(previous.resolvedRiskKeys),
        lastProcessedSegmentSequence=previous.lastProcessedSegmentSequence,
    )

    assert rebuilt.lastProcessedSegmentSequence == 4
