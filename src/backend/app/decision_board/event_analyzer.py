from __future__ import annotations


def analyze_events(events: list[dict]) -> list[dict]:
    signals = []

    for event in events:
        if event.get("type") == "RiskResolved":
            signals.append({
                "eventType": "risk_resolved",
                "title": event.get("sourceText"),
                "level": "INFO"
            })
        elif event.get("type"):
            signals.append({
                "eventType": "risk_created",
                "title": event.get("sourceText"),
                "level": "WARNING"
            })

    return signals
