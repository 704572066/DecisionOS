import re

from app.meetings.summary_context import SummaryContext
from app.meetings.summary_models import MeetingSummaryResult, SummaryCandidate, SummaryEvidence, SummaryItemCandidate


DECISION_MARKERS = re.compile(r"(最终决定|决定按|就按|按.+签|确认按|双方确认|同意按|接受.+并|推进签约)")
NON_DECISION_MARKERS = re.compile(r"(建议|希望|要求|提议|拒绝|不接受|撤回|作废|待确认|如果|可能)")
INVALID_STATUSES = {"rejected", "revoked", "superseded", "withdrawn", "proposed", "pending"}
ACTION_MARKERS = re.compile(r"(下一步|会后|由.+负责|请.+(?:跟进|完成|确认))")
ASSERTION_MARKERS = ("同意", "接受", "拒绝", "低于", "高于", "超过", "满足", "导致", "最终")


class SummaryGovernance:
    def validate(self, context: SummaryContext, candidate: SummaryCandidate, *, extraction_mode: str) -> MeetingSummaryResult:
        rejected: list[dict] = []
        accepted: dict[str, list[SummaryItemCandidate]] = {}
        for category in ("keyFacts", "decisions", "actionItems", "openIssues"):
            rows = []
            seen = set()
            for item in getattr(candidate, category):
                reason = self._reject_reason(context, category, item)
                normalized = " ".join(item.text.split())
                if reason:
                    rejected.append({"category": category, "text": normalized, "reason": reason})
                elif normalized and normalized not in seen:
                    rows.append(SummaryItemCandidate(text=normalized, sourceIds=list(dict.fromkeys(item.sourceIds))))
                    seen.add(normalized)
            accepted[category] = rows

        used_ids = list(dict.fromkeys(source_id for rows in accepted.values() for row in rows for source_id in row.sourceIds))
        evidence = [SummaryEvidence.model_validate(context.sources[source_id]) for source_id in used_ids]
        summary_parts = []
        for label, category in (("已确认事实", "keyFacts"), ("会议决策", "decisions"), ("后续行动", "actionItems"), ("未解决问题", "openIssues")):
            if accepted[category]:
                summary_parts.append(f"{label}：" + "；".join(row.text for row in accepted[category]))
        governed_summary = "。".join(summary_parts) + ("。" if summary_parts else "")
        if not governed_summary:
            governed_summary = "会议未形成通过来源校验的结构化结论。"
        return MeetingSummaryResult(
            meetingId=context.meeting_id,
            summary=governed_summary,
            keyFacts=accepted["keyFacts"], decisions=accepted["decisions"],
            actionItems=accepted["actionItems"], openIssues=accepted["openIssues"],
            evidence=evidence,
            diagnostics={"extractionMode": extraction_mode, "candidateCount": sum(len(getattr(candidate, x)) for x in accepted), "acceptedCount": sum(len(x) for x in accepted.values()), "rejectedCount": len(rejected), "rejected": rejected},
        )

    def _reject_reason(self, context: SummaryContext, category: str, item: SummaryItemCandidate) -> str | None:
        if not item.text.strip(): return "empty_text"
        if not item.sourceIds: return "missing_source"
        if any(source_id not in context.sources for source_id in item.sourceIds): return "unknown_source"
        sources = [context.sources[source_id] for source_id in item.sourceIds]
        if category in {"keyFacts", "decisions", "actionItems"} and any(source["sourceType"] in {"finding", "knowledge"} for source in sources):
            return "non_authoritative_source"
        statuses = {str((source.get("metadata") or {}).get("status") or "").lower() for source in sources}
        source_text = " ".join(str(source.get("text") or "") for source in sources)
        rejection_fact = category == "keyFacts" and re.search(r"(拒绝|不接受)", item.text) and re.search(r"(拒绝|不接受)", source_text)
        if statuses & INVALID_STATUSES and not rejection_fact: return "non_final_status"
        if category == "decisions":
            if not any(source["sourceType"] in {"transcript", "event", "semantic"} for source in sources): return "missing_decision_evidence"
            if not DECISION_MARKERS.search(source_text) or NON_DECISION_MARKERS.search(source_text): return "not_explicit_decision"
        if category == "keyFacts" and any(source["sourceType"] == "finding" for source in sources): return "finding_is_not_fact"
        if category == "keyFacts":
            if not set(re.findall(r"\d+(?:\.\d+)?%?|\d+天", item.text)).issubset(set(re.findall(r"\d+(?:\.\d+)?%?|\d+天", source_text))): return "unsupported_value"
            if any(marker in item.text and marker not in source_text for marker in ASSERTION_MARKERS): return "unsupported_assertion"
        if category == "actionItems" and not ACTION_MARKERS.search(source_text): return "not_explicit_action"
        return None


summary_governance = SummaryGovernance()

