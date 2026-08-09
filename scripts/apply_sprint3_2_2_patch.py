#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audio = ROOT / "src/backend/app/api/audio_ws.py"
text = audio.read_text(encoding="utf-8")

if "runtime_state_service.apply_transcript_event" not in text:
    import_marker = "from app.services.transcript_service import append_final_segment\n"
    if import_marker not in text:
        raise SystemExit("audio_ws transcript service import marker not found")
    text = text.replace(
        import_marker,
        import_marker
        + "from app.runtime.service import runtime_state_service\n",
        1,
    )

    marker = """        segment = append_result.segment
        await send_json_safe(
"""
    replacement = """        segment = append_result.segment

        # Sprint 3-2.2: update cached Runtime State from the latest final
        # transcript without another Retriever/LLM call.
        runtime_state_service.apply_transcript_event(
            meeting,
            text,
        )

        await send_json_safe(
"""
    if marker not in text:
        raise SystemExit("audio_ws append_result marker not found")
    text = text.replace(marker, replacement, 1)

    audio.write_text(text, encoding="utf-8")
    print("patched:", audio)

print("Sprint 3-2.2 patch applied.")
