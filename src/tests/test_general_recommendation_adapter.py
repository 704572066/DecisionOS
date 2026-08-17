from app.reasoning.models import Finding
from app.reasoning.recommendation_generator import RecommendationGenerator

finding = Finding(
    id="general-finding-test",
    type="risk",
    status="open",
    domain="general",
    subject="行业增长预测",
    title="行业未来三年增长50%的预测需要验证",
    summary="该预测直接影响投资判断。",
    severity="high",
    confidence=0.9,
    sourceIds=["runtime-context:test"],
    fingerprint="general:claim:test",
    attributes={
        "reasoningSource": "general",
        "generalFindingType": "claim",
        "noveltyKey": "growth-50",
        "suggestedAction": "要求提供行业增长预测的数据来源和第三方验证。",
    },
)

result = RecommendationGenerator().generate(
    meeting_id="meeting-test",
    context_id="context-test",
    findings=[finding],
)

item = result.recommendations[0]
print(item.model_dump(mode="json"))
assert item.title == finding.title
assert item.action == "要求提供行业增长预测的数据来源和第三方验证。"
assert item.attributes["reasoningSource"] == "general"
print("GENERAL RECOMMENDATION ADAPTER: OK")
