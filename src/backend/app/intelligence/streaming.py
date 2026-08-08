from __future__ import annotations
import json
import re
from dataclasses import dataclass, field

@dataclass(slots=True)
class ReminderStreamDelta:
    reminder_id: str
    field: str
    delta: str
    accumulated: str

@dataclass
class StructuredReminderStreamParser:
    reminder_id: str
    buffer: str = ""
    emitted: dict[str, str] = field(default_factory=dict)
    DISPLAY_FIELDS = ("title", "summary", "suggestion", "reason")

    def feed(self, text: str) -> list[ReminderStreamDelta]:
        if not text:
            return []
        self.buffer += text
        updates = []
        for field_name in self.DISPLAY_FIELDS:
            current = self._extract_string_value(field_name)
            if current is None:
                continue
            previous = self.emitted.get(field_name, "")
            if current == previous:
                continue
            delta = current[len(previous):] if current.startswith(previous) else current
            self.emitted[field_name] = current
            if delta:
                updates.append(ReminderStreamDelta(self.reminder_id, field_name, delta, current))
        return updates

    def _extract_string_value(self, field_name: str) -> str | None:
        match = re.search(
            rf'"{re.escape(field_name)}"\s*:\s*"((?:\\.|[^"\\])*)',
            self.buffer,
        )
        if not match:
            return None
        raw = match.group(1)
        try:
            return json.loads('"' + raw + '"')
        except json.JSONDecodeError:
            return raw.replace(r'\"','"').replace(r"\n","\n").replace(r"\t","\t")

def parse_sse_content(line: str) -> str | None:
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if not payload or payload == "[DONE]":
        return None
    data = json.loads(payload)
    choices = data.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) else None
