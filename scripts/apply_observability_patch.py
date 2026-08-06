#!/usr/bin/env python3
"""Patch the current Sprint 1.1 files with runtime observability hooks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"already patched: {path}")
        return
    if old not in text:
        raise SystemExit(f"expected text not found in {path}:\n{old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched: {path}")


audio = ROOT / "src/backend/app/api/audio_ws.py"
replace_once(
    audio,
    "from app.models.entities import Meeting\n",
    "from app.models.entities import Meeting\n"
    "from app.observability.runtime_metrics import runtime_metrics\n",
)
replace_once(
    audio,
    "    await websocket.accept()\n\n    db = SessionLocal()\n",
    "    await websocket.accept()\n"
    "    runtime_metrics.websocket_opened(meeting_id)\n\n"
    "    db = SessionLocal()\n",
)
replace_once(
    audio,
    '            logger.exception("Browser ASR session failed: meeting=%s", meeting_id)\n',
    '            runtime_metrics.record_error(\n'
    '                category="websocket.browser_asr",\n'
    '                message="Browser ASR session failed",\n'
    '                meeting_id=meeting_id,\n'
    '            )\n'
    '            logger.exception("Browser ASR session failed: meeting=%s", meeting_id)\n',
)
replace_once(
    audio,
    "        finally:\n            with suppress(RuntimeError):\n                await websocket.close()\n        return\n",
    "        finally:\n"
    "            runtime_metrics.websocket_closed(meeting_id)\n"
    "            with suppress(RuntimeError):\n"
    "                await websocket.close()\n"
    "        return\n",
)
replace_once(
    audio,
    '        logger.exception("Streaming ASR failed: meeting=%s", meeting_id)\n',
    '        runtime_metrics.record_error(\n'
    '            category="websocket.streaming_asr",\n'
    '            message=str(exc),\n'
    '            meeting_id=meeting_id,\n'
    '        )\n'
    '        logger.exception("Streaming ASR failed: meeting=%s", meeting_id)\n',
)
replace_once(
    audio,
    "    finally:\n        for task in (browser_task, provider_task):\n",
    "    finally:\n"
    "        runtime_metrics.websocket_closed(meeting_id)\n"
    "        for task in (browser_task, provider_task):\n",
)

# Track reminder duration without altering its business behavior.
reminder = ROOT / "src/backend/app/services/reminder_service.py"
replace_once(
    reminder,
    "from app.models.entities import Meeting\n",
    "from app.models.entities import Meeting\n"
    "from app.observability.runtime_metrics import runtime_metrics\n",
)
replace_once(
    reminder,
    "            result = analyze_meeting(db, meeting)\n",
    "            analysis_started = time.perf_counter()\n"
    "            result = analyze_meeting(db, meeting)\n"
    "            runtime_metrics.record_reminder_duration(\n"
    "                (time.perf_counter() - analysis_started) * 1000\n"
    "            )\n",
)

print("Observability hooks applied successfully.")
