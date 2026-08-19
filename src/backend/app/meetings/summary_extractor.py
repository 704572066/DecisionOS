import json
import logging
import re

from app.intelligence.llm import llm_provider
from app.meetings.summary_context import SummaryContext
from app.meetings.summary_models import SummaryCandidate, SummaryItemCandidate


SYSTEM_PROMPT = """You extract a meeting summary from a frozen, authoritative snapshot.
Return one JSON object with summary, keyFacts, decisions, actionItems, openIssues.
Every array item must have text and sourceIds, and every sourceId must be from availableSources.
Authority: final semanticState/decisionState > events/transcript > findings > recommendations.
Recommendations are never facts or decisions. Findings may support open issues only.
A decision requires explicit acceptance/commitment/decision language in transcript, event, or semantic evidence.
Rejected, revoked, superseded, proposed, requested, or unresolved conditions are not decisions.
Do not infer financial impact, acceptance, agreement, or resolution that is not explicit.
Use Chinese. Return JSON only."""
logger = logging.getLogger("decisionos.meetings.summary")


class MeetingSummaryExtractor:
    async def extract(self, context: SummaryContext) -> tuple[SummaryCandidate, str]:
        if llm_provider.enabled:
            try:
                payload = await llm_provider.generate_json(SYSTEM_PROMPT, json.dumps(context.llm_payload(), ensure_ascii=False), temperature=0.0)
                return SummaryCandidate.model_validate(payload), "llm"
            except Exception:
                logger.exception("Meeting summary extraction failed; using governed deterministic fallback")
                return self._deterministic(context), "deterministic_fallback"
        return self._deterministic(context), "deterministic"

    def _deterministic(self, context: SummaryContext) -> SummaryCandidate:
        facts: list[SummaryItemCandidate] = []
        decisions: list[SummaryItemCandidate] = []
        open_issues: list[SummaryItemCandidate] = []
        actions: list[SummaryItemCandidate] = []
        seen: set[str] = set()

        for source_id, source in context.sources.items():
            metadata = source.get("metadata") or {}
            source_type = source.get("sourceType")
            text = str(source.get("text") or "").strip()
            lowered = text.lower()
            status = str(metadata.get("status") or "").lower()
            role = str(metadata.get("role") or "").lower()
            if not text:
                continue
            if source_type in {"transcript", "event", "semantic"} and re.search(r"(客户.*(?:拒绝|不接受)|(?:拒绝|不接受).*(?:方案|条件|折扣))", text):
                if text not in seen:
                    facts.append(SummaryItemCandidate(text=text, sourceIds=[source_id])); seen.add(text)
            if status in {"rejected", "revoked", "superseded", "withdrawn"}:
                continue
            if source_type == "semantic" and status in {"confirmed", "accepted", "active"} and role in {"requirement", "acceptance", "commitment", "decision"}:
                if text not in seen:
                    facts.append(SummaryItemCandidate(text=text, sourceIds=[source_id])); seen.add(text)
            explicit = re.search(r"(最终决定|决定按|就按|按.+签|确认按|双方确认|同意按|接受.+并|推进签约)", text)
            if source_type in {"transcript", "event", "semantic"} and explicit and not re.search(r"(建议|希望|要求|拒绝|不接受|暂不|待确认|如果)", text):
                decisions.append(SummaryItemCandidate(text=text, sourceIds=[source_id]))
            if source_type == "transcript" and re.search(r"(下一步|会后|由.+负责|请.+(?:跟进|完成|确认))", text) and not re.search(r"(建议|可以考虑)", text):
                actions.append(SummaryItemCandidate(text=text, sourceIds=[source_id]))
            if source_type == "finding" and status != "resolved":
                open_issues.append(SummaryItemCandidate(text=text, sourceIds=[source_id]))

        transcript = str(context.snapshot.get("transcript") or "").strip()
        summary = transcript[-500:] if transcript else "会议未形成可总结的有效内容。"
        return SummaryCandidate(summary=summary, keyFacts=facts, decisions=decisions, actionItems=actions, openIssues=open_issues)


meeting_summary_extractor = MeetingSummaryExtractor()

