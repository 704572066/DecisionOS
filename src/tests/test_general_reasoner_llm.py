import asyncio
import json

from app.reasoning.general import (
    GeneralReasoningContextBuilder,
    GeneralReasoner,
)
from app.runtime.models import RuntimeState


async def main():
    state = RuntimeState(
        meetingId="meeting-investment-llm-test",
        projectId="project-investment-test",
        contextId="context-investment-test",
        objective="判断是否值得共同投资这个项目",
        canonicalContext=(
            "对方说：这个行业未来三年每年都会增长50%，"
            "我们的项目毛利至少能做到40%，已经有20家大客户，"
            "竞争对手基本进不来了。现在是最好的投资窗口，"
            "如果这个星期不决定，以后就没有机会了。"
        ),
        decisionFacts={},
        decisionState={},
        recentEvents=[],
        rerankedEvidence=[],
    )

    context = GeneralReasoningContextBuilder().build(
        state
    )

    result = await GeneralReasoner().reason(
        context
    )

    print(
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n=== SUMMARY ===")
    print("candidates:", len(result.candidates))
    print("findings:", len(result.findings))
    print("rejected:", len(result.rejected))
    print("backend errors:", result.diagnostics.backendErrors)


asyncio.run(main())
