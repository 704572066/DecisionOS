from app.context.models import BusinessContext
from app.intelligence.prompt_builder import build_prompt
from app.intelligence.reranker import RankedEvidence

def test_prompt_contains_traceable_evidence():
    context = BusinessContext(
        contextId="ctx",
        projectId="project",
        cleanTranscriptWindow="客户要求付款周期延长到180天。",
        topics=["付款"],
    )
    evidence = [
        RankedEvidence(
            item={
                "objectType": "decision",
                "objectId": "decision-1",
                "sourceType": "decision",
                "title": "历史账期决策",
                "summary": "超过120天需要增加担保。",
            },
            retrieval_score=.8,
            context_score=.2,
            final_score=.82,
            reasons=["付款议题增强"],
        )
    ]
    system, user = build_prompt(context, evidence)
    assert "不得虚构企业事实" in system
    assert "decision-1" in user
    assert "超过120天" in user
