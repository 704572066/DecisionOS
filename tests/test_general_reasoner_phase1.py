import asyncio
import json

from app.reasoning.general import (
    GeneralFindingCandidate,
    GeneralReasoner,
    GeneralReasonerBackend,
    GeneralReasoningContextBuilder,
)
from app.runtime.models import RuntimeState


class StaticBackend(GeneralReasonerBackend):
    async def analyze(self, context):
        return [
            GeneralFindingCandidate(
                id="candidate-growth",
                type="claim",
                domain="investment",
                subject="industryGrowth",
                title="行业增长预测需要验证",
                summary=(
                    "对方声称行业未来三年增长50%，"
                    "该主张会显著影响投资判断，但当前没有独立验证。"
                ),
                severity="high",
                confidence=0.91,
                decisionRelevance=0.95,
                specificity=0.95,
                evidenceDirectness=0.95,
                directlyObserved=True,
                evidenceSourceIds=[
                    context.contextSourceId,
                ],
                noveltyKey=(
                    "investment:industry-growth-50pct:unsupported"
                ),
                suggestedAction=(
                    "要求提供行业增长预测的数据来源和计算依据。"
                ),
            ),
            # Same novelty identity -> should be rejected as duplicate.
            GeneralFindingCandidate(
                id="candidate-growth-duplicate",
                type="claim",
                domain="investment",
                subject="industryGrowth",
                title="增长50%的依据需要核实",
                severity="medium",
                confidence=0.88,
                decisionRelevance=0.90,
                specificity=0.90,
                evidenceDirectness=0.90,
                directlyObserved=True,
                evidenceSourceIds=[
                    context.contextSourceId,
                ],
                noveltyKey=(
                    "investment:industry-growth-50pct:unsupported"
                ),
            ),
            # Low relevance -> Gate rejects.
            GeneralFindingCandidate(
                id="candidate-smalltalk",
                type="claim",
                title="普通背景信息",
                confidence=0.90,
                decisionRelevance=0.20,
                specificity=0.90,
                evidenceDirectness=0.90,
                directlyObserved=True,
                evidenceSourceIds=[
                    context.contextSourceId,
                ],
                noveltyKey="smalltalk:not-important",
            ),
        ]


async def main():
    state = RuntimeState(
        meetingId="meeting-investment-test",
        projectId="project-test",
        contextId="context-test",
        objective="判断是否参与该项目投资",
        canonicalContext=(
            "对方表示这个行业未来三年会增长50%，"
            "项目毛利可以达到40%，现在是最好的投资窗口。"
        ),
        decisionFacts={},
        decisionState={},
        recentEvents=[],
        rerankedEvidence=[],
    )

    context = GeneralReasoningContextBuilder().build(
        state
    )

    result = await GeneralReasoner(
        backend=StaticBackend()
    ).reason(context)

    print("\n=== SUMMARY ===")
    print(
        json.dumps(
            result.diagnostics.model_dump(
                mode="json"
            ),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n=== FINDINGS ===")
    for finding in result.findings:
        print(
            json.dumps(
                finding.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
                indent=2,
            )
        )

    print("\n=== REJECTED ===")
    for item in result.rejected:
        print(
            item.candidate.id,
            item.reason,
        )

    assert len(result.candidates) == 3
    assert len(result.findings) == 1
    assert len(result.rejected) == 2

    finding = result.findings[0]

    assert finding.type == "risk"
    assert (
        finding.attributes[
            "reasoningSource"
        ]
        == "general"
    )
    assert (
        finding.attributes[
            "generalFindingType"
        ]
        == "claim"
    )
    assert (
        finding.attributes[
            "suggestedAction"
        ]
        == "要求提供行业增长预测的数据来源和计算依据。"
    )

    print("\nGENERAL REASONER PHASE 1.1: OK")


asyncio.run(main())
