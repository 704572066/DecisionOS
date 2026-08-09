from __future__ import annotations


def build_decision_signals(events: list[dict]) -> list[dict]:
    return [
        {
            "title": "AI Decision Signal",
            "message": event.get("sourceText", ""),
            "eventType": event.get("type")
        }
        for event in events
    ]
