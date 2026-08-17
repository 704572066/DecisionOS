from __future__ import annotations

import json
from abc import ABC, abstractmethod

from pydantic import ValidationError

from app.intelligence.llm import llm_provider
from app.reasoning.general.context import (
    GeneralReasoningContext,
)
from app.reasoning.general.models import (
    GeneralFindingCandidate,
)
from app.reasoning.general.prompts import (
    GENERAL_REASONER_SYSTEM_PROMPT,
)


class GeneralReasonerBackend(ABC):
    @abstractmethod
    async def analyze(
        self,
        context: GeneralReasoningContext,
    ) -> list[GeneralFindingCandidate]:
        raise NotImplementedError


class NullGeneralReasonerBackend(
    GeneralReasonerBackend
):
    async def analyze(
        self,
        context: GeneralReasoningContext,
    ) -> list[GeneralFindingCandidate]:
        return []


class LLMGeneralReasonerBackend(
    GeneralReasonerBackend
):
    """
    LLM proposes candidates only.

    This backend has no authority to create active Findings. All output
    must pass FindingGate in GeneralReasoner.
    """

    async def analyze(
        self,
        context: GeneralReasoningContext,
    ) -> list[GeneralFindingCandidate]:

        if not llm_provider.enabled:
            raise RuntimeError(
                "LLM is not configured"
            )

        prompt = self._user_prompt(
            context
        )

        payload = await llm_provider.generate_json(
            GENERAL_REASONER_SYSTEM_PROMPT,
            prompt,
            temperature=0.1,
        )

        raw_candidates = payload.get(
            "candidates"
        )

        if not isinstance(
            raw_candidates,
            list,
        ):
            return []

        output: list[GeneralFindingCandidate] = []

        for raw in raw_candidates:
            if not isinstance(raw, dict):
                continue

            try:
                output.append(
                    GeneralFindingCandidate.model_validate(
                        raw
                    )
                )
            except ValidationError:
                continue

        return output

    @staticmethod
    def _user_prompt(
        context: GeneralReasoningContext,
    ) -> str:

        sources = [
            item.model_dump(
                mode="json"
            )
            for item in context.sources
        ]

        policy_findings = [
            item.model_dump(
                mode="json"
            )
            for item
            in context.activePolicyFindings
        ]

        payload = {
            "meetingId": context.meetingId,
            "contextId": context.contextId,
            "objective": context.objective,
            "canonicalContext": (
                context.canonicalContext
            ),
            "semanticState": (
                context.semanticState
            ),
            "decisionState": (
                context.decisionState
            ),
            "recentEvents": (
                context.recentEvents
            ),
            "activePolicyFindings": (
                policy_findings
            ),
            "dialogueHistory": (
                context.dialogueHistory
            ),
            "availableSources": sources,
            "currentContextSourceId": (
                context.contextSourceId
            ),
        }

        return (
            "GENERAL REASONING CONTEXT:\n"
            + json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            )
        )
