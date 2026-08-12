from __future__ import annotations

import json
import logging
from typing import Any

from app.intelligence.llm import llm_provider
from app.runtime.models import RuntimeState
from app.runtime.semantic_event_validator import semantic_event_validator
from app.runtime.semantic_models import SemanticEventCandidate, SemanticEventEnvelope

logger = logging.getLogger("decisionos.runtime.semantic")


SYSTEM_PROMPT = """You extract decision-relevant semantics from business meeting speech.
Return JSON only. Do not provide advice and do not invent facts.

Your output schema is:
{
  "events": [
    {
      "domain": "commercial|delivery|scope|resource|contract|commitment|approval|decision|unknown|other",
      "kind": "fact_change|constraint|commitment|dependency|scope_change|resource_constraint|liability|decision|unknown",
      "field": "stable camelCase field name or empty string",
      "value": "literal value from the utterance when useful",
      "normalizedValue": "normalized machine value when safely inferable, otherwise null",
      "relation": "<=|>=|=|requires|depends_on|conditional_on|adds|removes|replaces or empty string",
      "actor": "speaker/party when explicit, otherwise empty string",
      "target": "affected object when explicit, otherwise empty string",
      "status": "accepted|rejected|proposed|pending|confirmed|withdrawn or empty string",
      "sourceText": "the shortest supporting source span",
      "confidence": 0.0,
      "metadata": {}
    }
  ]
}

Important:
- Extract meaning, not keywords.
- A statement may contain several events.
- Preserve conditional commitments and approval dependencies.
- Delivery dates, scope changes, resource limits, liabilities, commitments, approvals and decisions are first-class.
- Do not infer previousValue. Runtime owns previous state.
- If there is no decision-relevant information, return {"events": []}.
"""


class SemanticEventExtractor:
    async def extract(
        self,
        text: str,
        previous: RuntimeState | None,
    ) -> list[SemanticEventCandidate]:
        source = " ".join((text or "").split())
        if not source or not llm_provider.enabled:
            return []

        state_summary = self._state_summary(previous)
        user_prompt = (
            "Current runtime state (context only; do not repeat it as a new event):\n"
            + json.dumps(state_summary, ensure_ascii=False)
            + "\n\nNew meeting utterance:\n"
            + source
        )

        try:
            payload = await llm_provider.generate_json(
                SYSTEM_PROMPT,
                user_prompt,
                temperature=0.0,
            )
            envelope = SemanticEventEnvelope.model_validate(payload)
            return semantic_event_validator.validate(
                envelope.events,
                source_text=source,
            )
        except Exception:
            logger.exception("Semantic event extraction failed")
            return []

    @staticmethod
    def _state_summary(previous: RuntimeState | None) -> dict[str, Any]:
        if previous is None:
            return {}
        return {
            "objective": previous.objective,
            "decisionFacts": previous.decisionFacts,
            "resolvedRiskKeys": previous.resolvedRiskKeys,
        }


semantic_event_extractor = SemanticEventExtractor()
