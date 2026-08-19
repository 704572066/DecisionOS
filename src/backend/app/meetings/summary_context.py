from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryContext:
    meeting_id: str
    snapshot: dict
    sources: dict[str, dict]

    def llm_payload(self) -> dict:
        return {
            "meetingId": self.meeting_id,
            "transcript": self.snapshot.get("transcript", ""),
            "semanticState": self.snapshot.get("semanticState", {}),
            "decisionState": self.snapshot.get("decisionState", {}),
            "recentEvents": self.snapshot.get("recentEvents") or self.snapshot.get("decisionBoard", {}).get("recentEvents", []),
            "findings": self.snapshot.get("findings", []),
            "recommendations": self.snapshot.get("recommendations", []),
            "availableSources": list(self.sources.values()),
        }


def build_summary_context(meeting_id: str, snapshot: dict) -> SummaryContext:
    sources: dict[str, dict] = {}
    for index, row in enumerate(snapshot.get("segments") or []):
        source_id = str(row.get("id") or f"transcript:{index}")
        sources[source_id] = {"sourceId": source_id, "sourceType": "transcript", "text": row.get("text", ""), "metadata": {"sequence": row.get("sequence")}}
    events = snapshot.get("recentEvents") or snapshot.get("decisionBoard", {}).get("recentEvents", [])
    for index, row in enumerate(events):
        source_id = str(row.get("eventId") or f"event:{index}")
        sources[source_id] = {"sourceId": source_id, "sourceType": "event", "text": row.get("sourceText", ""), "metadata": row}
    for domain, values in (snapshot.get("semanticState") or {}).items():
        for index, row in enumerate(values if isinstance(values, list) else []):
            source_id = str(row.get("eventId") or row.get("sourceId") or f"semantic:{domain}:{index}")
            sources[source_id] = {"sourceId": source_id, "sourceType": "semantic", "text": row.get("sourceText", ""), "metadata": {**row, "domain": domain}}
    for index, row in enumerate(snapshot.get("findings") or []):
        source_id = str(row.get("id") or f"finding:{index}")
        sources[source_id] = {"sourceId": source_id, "sourceType": "finding", "text": row.get("summary") or row.get("title", ""), "metadata": row}
    for index, row in enumerate(snapshot.get("evidence") or []):
        source_id = str(row.get("id") or f"knowledge:{index}")
        sources[source_id] = {"sourceId": source_id, "sourceType": "knowledge", "text": row.get("summary") or row.get("title", ""), "metadata": row}
    return SummaryContext(meeting_id=meeting_id, snapshot=snapshot, sources=sources)

