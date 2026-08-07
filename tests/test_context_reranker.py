from app.context.models import BusinessContext, ContextFact
from app.intelligence.reranker import rerank_context

def test_profit_policy_is_boosted_by_objective():
    context = BusinessContext(
        contextId="ctx",
        projectId="project",
        currentObjective="在保证利润率的前提下完成签约",
        cleanTranscriptWindow="客户要求整体价格下降18%，并希望付款周期延长到180天。",
        topics=["付款", "价格", "客户"],
        facts=[
            ContextFact(text="18%", factType="percentage", normalizedValue="18%"),
            ContextFact(text="180天", factType="duration", normalizedValue="180天"),
        ],
    )
    results = [
        {
            "itemId": "history",
            "objectType": "document",
            "objectId": "history",
            "sourceType": "document",
            "title": "历史成交复盘",
            "summary": "类似客户最终折扣为8%。",
            "score": 0.70,
        },
        {
            "itemId": "policy",
            "objectType": "evidence",
            "objectId": "policy",
            "sourceType": "policy",
            "title": "公司项目利润率规则",
            "summary": "项目目标毛利率不得低于18%；超过10%的折扣必须评估付款周期。",
            "score": 0.67,
        },
    ]
    ranked = rerank_context(context, results, top_k=2)
    assert ranked[0].item["objectId"] == "policy"
