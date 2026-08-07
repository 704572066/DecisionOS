from __future__ import annotations

import json
from app.context.models import BusinessContext
from app.intelligence.reranker import RankedEvidence

SYSTEM_PROMPT = """你是 DecisionOS 的企业会议决策提醒引擎。
你的职责是在会议进行过程中，基于当前上下文和给定的企业历史证据，生成少量、及时、可追溯的提醒。

必须遵守：
1. 只能使用提供的 Context 和 Evidence，不得虚构企业事实。
2. 每条提醒必须引用至少一个 Evidence source。
3. 优先提醒风险、历史约束、与当前目标冲突的信息；不要复述会议原文。
4. 不替管理者做最终决定。suggestion 只能是建议或待确认动作。
5. 最多生成 3 条提醒；没有足够价值时返回空数组。
6. confidence 代表基于当前证据的提醒可靠程度，不代表事实本身的绝对真实性。
7. 只返回 JSON，不要 Markdown。"""


def build_prompt(context: BusinessContext, evidence: list[RankedEvidence]) -> tuple[str, str]:
    evidence_payload = []
    for rank, row in enumerate(evidence, start=1):
        item = row.item
        evidence_payload.append(
            {
                "rank": rank,
                "objectType": item.get("objectType"),
                "objectId": item.get("objectId"),
                "sourceType": item.get("sourceType"),
                "title": item.get("title"),
                "content": item.get("summary"),
                "retrievalScore": round(row.retrieval_score, 4),
                "rerankScore": round(row.final_score, 4),
                "rerankReasons": row.reasons,
            }
        )

    user_payload = {
        "context": {
            "contextId": context.contextId,
            "projectId": context.projectId,
            "meetingId": context.meetingId,
            "intent": context.intent,
            "currentObjective": context.currentObjective,
            "canonicalMeetingContext": context.cleanTranscriptWindow,
            "topics": context.topics,
            "entities": [entity.model_dump() for entity in context.entities],
            "facts": [fact.model_dump() for fact in context.facts],
            "constraints": [c.model_dump() for c in context.constraints],
        },
        "evidence": evidence_payload,
        "outputContract": {
            "reminders": [
                {
                    "type": "risk|suggestion|history|question|opportunity",
                    "title": "简短标题",
                    "summary": "为什么此刻值得提醒",
                    "suggestion": "建议下一步动作，可为空",
                    "reason": "证据与当前上下文之间的关系",
                    "sources": [
                        {
                            "type": "Evidence中的sourceType或objectType",
                            "id": "Evidence中的objectId",
                            "title": "Evidence标题",
                            "score": 0.0,
                        }
                    ],
                    "confidence": 0.0,
                }
            ]
        },
    }
    return SYSTEM_PROMPT, json.dumps(user_payload, ensure_ascii=False)
