#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding="utf-8")
    if new in text:
        print("already patched:", path)
        return
    if old not in text:
        raise SystemExit(f"expected marker not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("patched:", path)

audio = ROOT / "src/backend/app/api/audio_ws.py"
replace_once(
    audio,
    "        result = realtime_reminder_coordinator.analyze_if_due(db, meeting)\n",
    "        result = await realtime_reminder_coordinator.analyze_if_due(db, meeting)\n",
)

text = audio.read_text(encoding="utf-8")
if '"rerankedEvidence": result.get("rerankedEvidence")' not in text:
    old = '''                    "context": result.get("context"),
                },
'''
    new = '''                    "context": result.get("context"),
                    "diagnostics": result.get("diagnostics"),
                    "rerankedEvidence": result.get("rerankedEvidence"),
                },
'''
    if old not in text:
        raise SystemExit("audio_ws reminder.batch marker not found")
    audio.write_text(text.replace(old, new, 1), encoding="utf-8")

config = ROOT / "src/backend/app/core/config.py"
text = config.read_text(encoding="utf-8")
if "llm_timeout_seconds:" not in text:
    marker = '    openai_model: str = "gpt-4.1-mini"\n'
    addition = (
        marker
        + "    llm_timeout_seconds: float = 30.0\n"
        + "    llm_json_mode: bool = False\n"
        + "    reminder_temperature: float = 0.1\n"
        + "    reminder_retrieval_top_k: int = 8\n"
        + "    reminder_evidence_top_k: int = 5\n"
    )
    if marker not in text:
        raise SystemExit("config openai_model marker not found")
    config.write_text(text.replace(marker, addition, 1), encoding="utf-8")
    print("patched:", config)

main = ROOT / "src/backend/app/main.py"
text = main.read_text(encoding="utf-8")
if "ai_reminder_router" not in text:
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from app.api."):
            insert_at = i + 1
    lines.insert(insert_at, "from app.api.ai_reminder import router as ai_reminder_router")
    text = "\n".join(lines) + "\n"

    include_line = "app.include_router(ai_reminder_router)"
    if include_line not in text:
        marker = "app.include_router(router)"
        if marker in text:
            text = text.replace(marker, marker + "\n" + include_line, 1)
        else:
            startup_marker = '@app.on_event("startup")'
            if startup_marker not in text:
                raise SystemExit("main.py include marker not found")
            text = text.replace(startup_marker, include_line + "\n\n" + startup_marker, 1)

    main.write_text(text, encoding="utf-8")
    print("patched:", main)

print("Sprint 2-3 patch applied.")
