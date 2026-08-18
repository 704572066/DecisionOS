import json

from app.decision_board.builder import DecisionBoardBuilder
from app.reasoning.models import (
    Finding,
    ReasoningDiagnostics,
    ReasoningResult,
)
from app.reasoning.recommendation_models import Recommendation
from app.runtime.models import RuntimeState


builder = DecisionBoardBuilder()


state = RuntimeState(
    meetingId="meeting-test",
    projectId="project-test",
    contextId="context-test",
    objective="测试决策",
    rerankedEvidence=[
        {
            "objectId": "policy-test",
            "sourceType": "policy",
            "title": "测试政策",
            "summary": "测试规则",
            "rerankScore": 0.95,
        },
        {
            "objectId": "decision-test",
            "sourceType": "decision",
            "title": "历史决策",
            "summary": "历史依据",
            "rerankScore": 0.80,
        },
    ],
    decisionFacts={
        "semanticState": {
            "commercial": [
                {
                    "domain": "commercial",
                    "field": "discountPercent",
                    "value": 15,
                    "status": "confirmed",
                }
            ]
        }
    },
    recentEvents=[],
)

finding = Finding(
    id="finding-test",
    type="dependency",
    status="open",
    domain="commercial",
    subject="discountPercent",
    title="超过10%的折扣必须评估付款周期",
    summary="当前缺少付款周期评估。",
    severity="high",
    sourceIds=["policy-test"],
    fingerprint="dependency:test",
)

recommendation = Recommendation(
    id="recommendation-test",
    meetingId="meeting-test",
    findingId="finding-test",
    status="open",
    title="完成付款周期评估",
    action="在继续当前决策前完成付款周期评估。",
    priority="high",
    sourceIds=["policy-test"],
    fingerprint="recommendation:test",
)

reasoning = ReasoningResult(
    meetingId="meeting-test",
    contextId="context-test",
    projectId="project-test",
    findings=[finding],
    recommendations=[recommendation],
    diagnostics=ReasoningDiagnostics(
        evaluationContextBuilt=True,
        activeFindingCount=1,
        activeRecommendationCount=1,
    ),
)

board = builder.build(
    state=state,
    reasoning=reasoning,
)

print(json.dumps(
    board.model_dump(mode="json"),
    ensure_ascii=False,
    indent=2,
))

payload = board.model_dump(mode="json")
assert "status" not in payload
assert "decisionReadiness" not in payload
assert len(payload["risks"]) == 1
assert len(payload["actions"]) == 1
assert len(payload["evidence"]) == 2
print("\nLEGACY CLEANUP ASSERTIONS: OK")
