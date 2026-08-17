from app.reasoning.general.context import (
    GeneralReasoningContextBuilder,
)
from app.runtime.models import RuntimeState


state = RuntimeState(
    meetingId="meeting-grounding-test",
    projectId="project-test",
    contextId="context-test",
    objective="测试",
    canonicalContext=(
        "历史对话窗口里可能仍包含已被替代的条件。"
    ),
    decisionFacts={
        "semanticState": {
            "commercial": [
                {
                    "domain": "commercial",
                    "field": "discountPercent",
                    "value": 10,
                    "role": "requirement",
                    "actor": "customer",
                    "status": "confirmed",
                    "confidence": 0.95,
                    "sourceText": "客户只接受10%",
                    "eventId": "event-current-10",
                }
            ]
        }
    },
    decisionState={},
    recentEvents=[],
    rerankedEvidence=[
        {
            "objectId": "policy-test",
            "sourceType": "policy",
            "title": "公司规则",
            "summary": "超过10%需要评估。",
            "rerankScore": 1.0,
        },
        {
            "objectId": "decision-history",
            "sourceType": "decision",
            "title": "历史决策",
            "summary": "历史上曾采用8%。",
            "rerankScore": 0.9,
        },
    ],
)

context = GeneralReasoningContextBuilder().build(
    state
)

sources = context.source_by_id()

conversation = sources[
    context.contextSourceId
]

policy = sources["policy-test"]
decision = sources["decision-history"]
semantic = sources["event-current-10"]

print("conversation:", conversation.model_dump(mode="json"))
print("policy:", policy.model_dump(mode="json"))
print("decision:", decision.model_dump(mode="json"))
print("semantic:", semantic.model_dump(mode="json"))

assert conversation.sourceType == "conversation_text"
assert conversation.metadata["currentStateAuthority"] is False

assert policy.metadata["normativeReference"] is True
assert policy.metadata["historicalReference"] is False

assert decision.metadata["historicalReference"] is True
assert decision.metadata["normativeReference"] is False

assert semantic.metadata["authority"] == "semantic_state"
assert semantic.metadata["currentStateAuthority"] is True

print("PHASE 2.1 SOURCE AUTHORITY: OK")
