import asyncio

from app.reasoning import ReasoningService
from app.reasoning.constraint_compiler import ConstraintCompiler, NullConstraintCompilerBackend
from app.reasoning.finding_set_evaluator import FindingSetEvaluator
from app.reasoning.general import GeneralFindingCandidate, GeneralReasoner
from app.reasoning.general.backend import GeneralReasonerBackend
from app.reasoning.recommendation_set_evaluator import RecommendationSetEvaluator
from app.reasoning.snapshot_store import ReasoningSnapshotStore
from app.runtime.models import RuntimeState


class StaticGeneralBackend(GeneralReasonerBackend):
    async def analyze(self, context):
        return [
            GeneralFindingCandidate(
                id="cand-growth",
                type="claim",
                title="行业增长预测需要验证",
                subject="industryGrowth",
                severity="high",
                confidence=0.9,
                decisionRelevance=0.9,
                specificity=0.95,
                evidenceDirectness=1.0,
                directlyObserved=True,
                evidenceSourceIds=[context.contextSourceId],
                noveltyKey="growth-50",
                suggestedAction="要求提供行业增长预测的数据来源。",
            )
        ]


async def main():
    service = ReasoningService(
        compiler=ConstraintCompiler(
            backend=NullConstraintCompilerBackend()
        ),
        finding_evaluator=FindingSetEvaluator(),
        general_reasoner_instance=GeneralReasoner(
            backend=StaticGeneralBackend()
        ),
        recommendation_evaluator=RecommendationSetEvaluator(),
        snapshot_store=ReasoningSnapshotStore(),
    )

    state = RuntimeState(
        meetingId="meeting-phase2-test",
        projectId="project-test",
        contextId="context-phase2-test",
        objective="判断是否投资",
        canonicalContext="对方声称行业未来三年增长50%。",
        decisionFacts={},
        decisionState={},
        recentEvents=[],
        rerankedEvidence=[],
    )

    result = await service.get_or_reason(state)

    print("findings:", len(result.findings))
    print("recommendations:", len(result.recommendations))
    print("diagnostics:", result.diagnostics.model_dump(mode="json"))

    assert len(result.findings) == 1
    assert result.findings[0].attributes["reasoningSource"] == "general"
    assert len(result.recommendations) == 1
    assert result.recommendations[0].action == "要求提供行业增长预测的数据来源。"
    assert result.diagnostics.generalFindingCount == 1
    assert result.diagnostics.mergedFindingCount == 1

    cached = await service.get_or_reason(state)
    assert cached is result

    print("GENERAL REASONER PHASE 2 INTEGRATION: OK")


asyncio.run(main())
