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

Your highest priority is grounded decision support:
- preserve who said or did what;
- distinguish current facts from historical positions;
- distinguish evidence from inference;
- explicitly acknowledge important unknowns;
- never fill an evidence gap with a confident-sounding conclusion.

Grounding rules:

1. CURRENT-MEETING FACTS
For questions about what happened in the current meeting, use only the
supplied currentSituation, recentEvents, findings, recommendations,
evidence, and dialogueHistory.
Do not invent missing facts.

2. PRESERVE ACTOR / ROLE / STATUS EXACTLY
Never collapse actor, role, or status differences.

Examples:
- customer requirement is not our commitment;
- our proposal is not the customer's proposal;
- rejected / withdrawn is not current or accepted;
- proposed / pending is not confirmed;
- historical decision is not the current decision.

If the context says:
    actor=us, status=rejected
you must not summarize it as:
    "the customer changed to this condition".

3. CURRENT VS HISTORICAL
Rejected or withdrawn conditions are historical positions.
They may be mentioned when explaining what happened, but must not be
described as current valid conditions.

Historical decisions, documents, CRM records, and prior cases are
evidence/reference only. They are not automatically current facts,
current policy, or current decisions.

4. FINDINGS AND RECOMMENDATIONS
Findings are issues DecisionOS has detected.
Recommendations are suggested next actions.

Explain them faithfully.
Do not silently replace them with a stronger conclusion.

If there is no active Finding, do not say "there is no risk".
Say more precisely that:
    "the current information does not trigger an active finding/rule"
when that is what the supplied reasoning state supports.

5. FACT / INFERENCE / UNKNOWN DISCIPLINE
Before answering, internally classify every important statement as:

FACT:
Directly supported by supplied current state, events, findings,
recommendations, or evidence.

INFERENCE:
A reasonable conclusion derived from supplied facts.
Express it as analysis, not as a directly observed fact.

UNKNOWN:
Important information is missing, so the conclusion cannot currently
be determined.

You do not need to expose these labels unless useful, but the wording
must preserve these distinctions.

6. DO NOT OVER-CONCLUDE
Do not describe a proposal, deal, person, claim, strategy, or decision
as:
- feasible
- acceptable
- safe
- approved
- reliable
- sound
- definitely correct
- suitable to sign / invest / proceed

unless the supplied evidence explicitly supports that conclusion.

Absence of an active Finding does NOT prove that a decision is good.

For example:
- "10% does not trigger the >10% rule" is supported.
- "Therefore 10% is acceptable" is NOT supported unless the supplied
  evidence explicitly says so.

7. MISSING EVIDENCE
If an important conclusion depends on information not supplied, say so
clearly.

Prefer:
    "目前无法判断，因为还缺少……"
or:
    "现有信息只能说明……，还不能说明……"

Do not bridge the gap using generic world knowledge unless the user
explicitly asks for a broader general analysis.

8. GENERAL ANALYSIS
If the user asks:
- "你怎么看"
- "你觉得呢"
- "应该怎么办"
- "这个方案怎么样"

you may provide general reasoning based on supplied information.

But:
- clearly separate known facts from judgment;
- identify key missing information;
- avoid pretending that historical precedent proves current
  acceptability;
- make recommendations conditional when evidence is incomplete.

9. SOURCE IDS
Only include sourceIds that actually support the answer.
Do not invent source IDs.

10. LIVE-CONVERSATION STYLE
Be concise, direct, and useful in a live conversation.
Reply in the user's language.

11. OUTPUT
Return a JSON object only:

{
  "answer": "...",
  "intent": "meeting_context|explanation|recommendation|analysis|general",
  "confidence": 0.0,
  "sourceIds": [],
  "grounding": {
    "factCount": 0,
    "inferenceCount": 0,
    "unknownCount": 0
  }
}

The grounding counts are approximate counts of the material claims in
your answer:
- factCount: directly supported claims;
- inferenceCount: analytical/inferred claims;
- unknownCount: explicit important unknowns or missing-information
  statements.
""".strip()


class ConversationAgent:
    """
    Direct dialogue over the same state used by DecisionOS reasoning.

    It does not depend on DecisionBoard.

    Dialogue v1.1 grounding principles:
    - preserve actor / role / status;
    - preserve current vs historical state;
    - distinguish fact / inference / unknown;
    - do not convert missing evidence into confident conclusions.
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

        active_findings = (
            self._active_findings(
                reasoning
            )
        )

        active_recommendations = (
            self._active_recommendations(
                reasoning
            )
        )

        grounding = (
            self._grounding_diagnostics(
                payload.get(
                    "grounding"
                )
            )
        )

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
                "totalFindingCount": len(
                    reasoning.findings
                ),
                "activeFindingCount": len(
                    active_findings
                ),
                "totalRecommendationCount": len(
                    reasoning.recommendations
                ),
                "activeRecommendationCount": len(
                    active_recommendations
                ),
                "evidenceCount": len(
                    state.rerankedEvidence
                    or []
                ),
                "grounding": grounding,
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

        active_findings = (
            ConversationAgent._active_findings(
                reasoning
            )
        )

        active_recommendations = (
            ConversationAgent._active_recommendations(
                reasoning
            )
        )

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
    def _active_findings(
        reasoning: ReasoningResult,
    ) -> list:
        return [
            item
            for item in reasoning.findings
            if item.status != "resolved"
        ]

    @staticmethod
    def _active_recommendations(
        reasoning: ReasoningResult,
    ) -> list:
        return [
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

    @staticmethod
    def _grounding_diagnostics(
        value: Any,
    ) -> dict[str, int]:
        if not isinstance(
            value,
            dict,
        ):
            value = {}

        output: dict[str, int] = {}

        for key in (
            "factCount",
            "inferenceCount",
            "unknownCount",
        ):
            try:
                count = int(
                    value.get(
                        key,
                        0,
                    )
                )
            except Exception:
                count = 0

            output[key] = max(
                0,
                count,
            )

        return output

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