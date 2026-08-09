#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audio = ROOT / "src/backend/app/api/audio_ws.py"
text = audio.read_text(encoding="utf-8")

# 1. Import Runtime State service.
import_line = "from app.runtime.service import runtime_state_service\n"
if import_line not in text:
    # Prefer placing it near other app.* service imports.
    candidates = [
        "from app.services.transcript_service import append_final_segment\n",
        "from app.services.reminder_service import realtime_reminder_coordinator\n",
        "from app.models.entities import Meeting\n",
    ]
    marker = next((m for m in candidates if m in text), None)
    if marker is None:
        raise SystemExit(
            "Could not find a safe import insertion point in audio_ws.py"
        )
    text = text.replace(marker, marker + import_line, 1)

# 2. Insert immediately after the persisted segment assignment.
call_marker = "runtime_state_service.apply_transcript_event("
if call_marker not in text:
    exact_line = "        segment = append_result.segment\n"
    if exact_line not in text:
        # Tolerate 4-space indentation or extra whitespace.
        lines = text.splitlines(keepends=True)
        target_index = None
        target_indent = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "segment = append_result.segment":
                target_index = i
                target_indent = line[: len(line) - len(line.lstrip())]
                break

        if target_index is None:
            # Print nearby append_result occurrences to make failures actionable.
            nearby = [
                f"{i+1}: {line.rstrip()}"
                for i, line in enumerate(lines)
                if "append_result" in line or "segment =" in line
            ]
            detail = "\n".join(nearby[:20]) or "(no append_result/segment lines found)"
            raise SystemExit(
                "Could not find `segment = append_result.segment`.\n"
                "Nearby lines:\n" + detail
            )

        block = (
            "\n"
            f"{target_indent}# Sprint 3-2.2: lightweight Runtime State event update.\n"
            f"{target_indent}# No Retriever / Embedding / LLM call here.\n"
            f"{target_indent}runtime_state_service.apply_transcript_event(\n"
            f"{target_indent}    meeting,\n"
            f"{target_indent}    text,\n"
            f"{target_indent})\n"
        )
        lines.insert(target_index + 1, block)
        text = "".join(lines)
    else:
        block = """        segment = append_result.segment

        # Sprint 3-2.2: lightweight Runtime State event update.
        # No Retriever / Embedding / LLM call here.
        runtime_state_service.apply_transcript_event(
            meeting,
            text,
        )
"""
        text = text.replace(exact_line, block, 1)

audio.write_text(text, encoding="utf-8")
print("Sprint 3-2.2 audio_ws hotfix v2 applied:", audio)
