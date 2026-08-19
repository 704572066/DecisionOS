from __future__ import annotations

import json
import re
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

        historical = self._historical_decision_candidates(context)
        if not llm_provider.enabled:
            return historical

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

        existing = {item.noveltyKey for item in output}
        output.extend(item for item in historical if item.noveltyKey not in existing)
        return output

    @staticmethod
    def _historical_decision_candidates(context: GeneralReasoningContext) -> list[GeneralFindingCandidate]:
        current = (context.decisionState or {}).get("commercial") or {}
        if not current:
            return []
        output = []
        for source in context.sources:
            if source.sourceType != "decision_memory":
                continue
            old_discount = re.search(r"(\d+(?:\.\d+)?)\s*%", source.summary or "")
            old_payment = re.search(r"(\d+)\s*天", source.summary or "")
            differences = []
            if old_discount and current.get("discountPercent") is not None and float(old_discount.group(1)) != float(current["discountPercent"]):
                differences.append(f"当前折扣{float(current['discountPercent']):g}%偏离历史决策{float(old_discount.group(1)):g}%")
            if old_payment and current.get("paymentTermDays") is not None and int(old_payment.group(1)) != int(current["paymentTermDays"]):
                differences.append(f"当前付款周期{int(current['paymentTermDays'])}天偏离历史决策{int(old_payment.group(1))}天")
            if not differences:
                continue
            output.append(GeneralFindingCandidate(
                type="contradiction", domain="decision_memory", subject="commercial_terms",
                title="当前条件与历史会议决策存在偏离", summary="；".join(differences) + f"。依据：{source.title}",
                severity="medium", confidence=.95, decisionRelevance=.92, specificity=.95,
                evidenceDirectness=.95, directlyObserved=True, directlyNeeded=False,
                evidenceSourceIds=[context.contextSourceId, source.id],
                noveltyKey=f"decision-memory-deviation:{source.id}",
                suggestedAction="确认本次条件是否明确替代此前会议决策，并记录变更原因。",
                attributes={"historicalDecisionMemoryId": source.id, "authority": "historical_reference"},
            ))
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
            "currentSituation": {
                "semanticState": (
                    context.semanticState
                ),
                "decisionState": (
                    context.decisionState
                ),
            },
            "recentEvents": (
                context.recentEvents
            ),
            "conversationText": (
                context.canonicalContext
            ),
            "activePolicyFindings": (
                policy_findings
            ),
            "dialogueHistory": (
                context.dialogueHistory
            ),
            "availableSources": sources,
            "conversationTextSourceId": (
                context.contextSourceId
            ),
            "authorityOrder": [
                "currentSituation",
                "recentEvents",
                "conversationText",
                "availableSources",
            ],
        }

        return (
            "GENERAL REASONING CONTEXT:\n"
            + json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            )
        )

