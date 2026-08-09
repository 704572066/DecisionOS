#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audio = ROOT / "src/backend/app/api/audio_ws.py"
text = audio.read_text(encoding="utf-8")

# 1. Import Runtime State service.
if "from app.runtime.service import runtime_state_service" not in text:
    marker = "from app.services.transcript_service import append_final_segment\n"
    if marker not in text:
        raise SystemExit("transcript_service import marker not found")
    text = text.replace(
        marker,
        marker + "from app.runtime.service import runtime_state_service\n",
        1,
    )

# 2. Update Runtime State immediately after the final segment is persisted.
if "runtime_state_service.apply_transcript_event(" not in text:
    marker = """        segment = append_result.segment
        await send_json_safe(
"""
    replacement = """        segment = append_result.segment

        # Sprint 3-2.2:
        # Update cached Runtime State from this final transcript.
        # This is deterministic and does not invoke Retriever / Embedding / LLM.
        runtime_state_service.apply_transcript_event(
            meeting,
            text,
        )

        await send_json_safe(
"""
    if marker not in text:
        raise SystemExit("segment/send_json marker not found")
    text = text.replace(marker, replacement, 1)

audio.write_text(text, encoding="utf-8")
print("Sprint 3-2.2 audio_ws hotfix applied:", audio)
