from __future__ import annotations

import json
from typing import Any

from app.dialogue.models import (
    DialogueResponse,
    DialogueTurn,
)
from app.intelligence.llm import llm_provider
from app.reasoning.models import (
    ReasoningResult,
)
from app.runtime.models import RuntimeState


SYSTEM_PROMPT = """
You are DecisionOS Conversation Agent, an AI decision companion.

Your job is to answer the user's direct question using the supplied
current situation and reasoning state.

Rules:
1. For questions about what happened in the current meeting, use only
   supplied RuntimeState / recent events / reasoning evidence. Do not
   invent missing facts.
2. Clearly distinguish facts from your own analysis or inference.
3. Findings are issues DecisionOS has detected. Recommendations are
   suggested next actions. Explain them faithfully rather than
   silently replacing them.
4. Historical decisions/documents/policies are evidence, not
   automatically current facts.
5. Rejected or withdrawn conditions are historical positions and must
   not be described as currently accepted conditions.
6. If the user asks "what do you think", you may provide general
   reasoning based on supplied information, but explicitly state major
   uncertainty or missing evidence.
7. Be concise and useful in a live conversation.
8. Reply in the user's language.
9. Return a JSON object only:

{
  "answer": "...",
  "intent": "meeting_context|explanation|recommendation|analysis|general",
  "confidence": 0.0,
  "sourceIds": []
}
""".strip()


class ConversationAgent:
    """
    Direct dialogue over the same state used by DecisionOS reasoning.

    It does not depend on DecisionBoard.
    """

    async def answer(
        self,
        *,
        meeting_id: str,
        conversation_id: str,
        question: str,
        state: RuntimeState,
        reasoning: ReasoningResult,
        history: list[DialogueTurn],
    ) -> DialogueResponse:

        if not llm_provider.enabled:
            raise RuntimeError(
                "LLM is not configured"
            )

        context = self._context_payload(
            state=state,
            reasoning=reasoning,
            history=history,
        )

        user_prompt = (
            "CURRENT DECISION CONTEXT:\n"
            + json.dumps(
                context,
                ensure_ascii=False,
                default=str,
            )
            + "\n\nUSER QUESTION:\n"
            + question.strip()
        )

        payload = await llm_provider.generate_json(
            SYSTEM_PROMPT,
            user_prompt,
            temperature=0.1,
        )

        answer = str(
            payload.get("answer")
            or ""
        ).strip()

        if not answer:
            answer = (
                "当前信息不足以回答这个问题。"
            )

        intent = str(
            payload.get("intent")
            or "general"
        )

        allowed_intents = {
            "meeting_context",
            "explanation",
            "recommendation",
            "analysis",
            "general",
        }

        if intent not in allowed_intents:
            intent = "general"

        try:
            confidence = float(
                payload.get(
                    "confidence",
                    0.5,
                )
            )
        except Exception:
            confidence = 0.5

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        source_ids = payload.get(
            "sourceIds"
        )

        if not isinstance(
            source_ids,
            list,
        ):
            source_ids = []

        source_ids = [
            str(item)
            for item in source_ids
            if item
        ]

        valid_source_ids = (
            self._valid_source_ids(
                state=state,
                reasoning=reasoning,
            )
        )

        source_ids = [
            item
            for item in source_ids
            if item in valid_source_ids
        ]

        return DialogueResponse(
            meetingId=meeting_id,
            conversationId=(
                conversation_id
            ),
            answer=answer,
            intent=intent,
            confidence=confidence,
            sourceIds=source_ids,
            diagnostics={
                "historyTurnCount": len(
                    history
                ),
                "findingCount": len(
                    reasoning.findings
                ),
                "recommendationCount": len(
                    reasoning.recommendations
                ),
                "evidenceCount": len(
                    state.rerankedEvidence
                    or []
                ),
            },
        )

    @staticmethod
    def _context_payload(
        *,
        state: RuntimeState,
        reasoning: ReasoningResult,
        history: list[DialogueTurn],
    ) -> dict[str, Any]:

        decision_facts = dict(
            state.decisionFacts
            or {}
        )

        active_findings = [
            item
            for item in reasoning.findings
            if item.status != "resolved"
        ]

        active_recommendations = [
            item
            for item
            in reasoning.recommendations
            if item.status
            not in {
                "obsolete",
                "completed",
                "dismissed",
            }
        ]

        evidence = []

        for item in list(
            state.rerankedEvidence
            or []
        )[:8]:
            evidence.append(
                {
                    "id": (
                        item.get("objectId")
                        or item.get("itemId")
                        or ""
                    ),
                    "type": (
                        item.get("sourceType")
                        or item.get("objectType")
                        or ""
                    ),
                    "title": item.get(
                        "title",
                        "",
                    ),
                    "summary": item.get(
                        "summary",
                        "",
                    ),
                    "score": (
                        item.get(
                            "rerankScore"
                        )
                        or item.get(
                            "score"
                        )
                        or 0
                    ),
                }
            )

        return {
            "meeting": {
                "meetingId": state.meetingId,
                "projectId": state.projectId,
                "objective": state.objective,
                "canonicalContext": (
                    state.canonicalContext
                ),
                "topics": list(
                    state.topics
                    or []
                ),
            },

            "currentSituation": {
                "semanticState": (
                    decision_facts.get(
                        "semanticState",
                        {},
                    )
                ),
                "decisionState": dict(
                    state.decisionState
                    or {}
                ),
            },

            "recentEvents": list(
                state.recentEvents
                or []
            )[-12:],

            "findings": [
                item.model_dump(
                    mode="json"
                )
                for item in active_findings
            ],

            "recommendations": [
                item.model_dump(
                    mode="json"
                )
                for item
                in active_recommendations
            ],

            "evidence": evidence,

            "dialogueHistory": [
                {
                    "role": item.role,
                    "content": item.content,
                }
                for item in history[-8:]
            ],
        }

    @staticmethod
    def _valid_source_ids(
        *,
        state: RuntimeState,
        reasoning: ReasoningResult,
    ) -> set[str]:

        output: set[str] = set()

        for item in (
            state.rerankedEvidence
            or []
        ):
            source_id = (
                item.get("objectId")
                or item.get("itemId")
            )

            if source_id:
                output.add(
                    str(source_id)
                )

        for finding in reasoning.findings:
            output.update(
                finding.sourceIds
            )

        for recommendation in (
            reasoning.recommendations
        ):
            output.update(
                recommendation.sourceIds
            )

        for event in (
            state.recentEvents
            or []
        ):
            event_id = event.get(
                "eventId"
            )

            if event_id:
                output.add(
                    str(event_id)
                )

        return output


conversation_agent = ConversationAgent()
