#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Backend duplicate suppression.
audio = ROOT / "src/backend/app/api/audio_ws.py"
text = audio.read_text(encoding="utf-8")

if "streaming_context_keys:" not in text:
    marker = "streaming_reminder_tasks: set[asyncio.Task] = set()\n"
    if marker not in text:
        raise SystemExit("Sprint 2-3.1 streaming state not found in audio_ws.py")

    addition = marker + """
streaming_context_keys: dict[str, str] = {}
streaming_context_lock = asyncio.Lock()

def reminder_context_key(context) -> str:
    canonical = " ".join(
        (context.cleanTranscriptWindow or "").replace("\\n", " ").split()
    )
    facts = sorted(
        str(fact.normalizedValue or fact.text)
        for fact in context.facts
        if (fact.normalizedValue or fact.text)
    )
    return canonical + "||" + "|".join(facts)

async def reserve_reminder_context(meeting_id: str, context) -> bool:
    key = reminder_context_key(context)
    if not key.strip("|"):
        return False
    async with streaming_context_lock:
        previous = streaming_context_keys.get(meeting_id)
        if previous == key:
            return False
        streaming_context_keys[meeting_id] = key
        return True

def clear_reminder_context(meeting_id: str) -> None:
    streaming_context_keys.pop(meeting_id, None)

"""
    text = text.replace(marker, addition, 1)

    marker2 = """        context = build_meeting_context(db, meeting)
        retrieval = await hybrid_retriever.search(
"""
    replacement2 = """        context = build_meeting_context(db, meeting)

        if not await reserve_reminder_context(meeting_id, context):
            logger.info(
                "Skipped duplicate AI reminder context: meeting=%s",
                meeting_id,
            )
            return

        retrieval = await hybrid_retriever.search(
"""
    if marker2 not in text:
        raise SystemExit("Context marker not found in stream_ai_reminder")
    text = text.replace(marker2, replacement2, 1)

    audio.write_text(text, encoding="utf-8")
    print("patched:", audio)

# Frontend modal.
front = ROOT / "src/frontend/src/main.tsx"
text = front.read_text(encoding="utf-8")

old_open = """      {decisionCandidate && (
        <section className="decision-candidate-panel">
"""
new_open = """      {decisionCandidate && (
        <div
          className="decision-modal-backdrop"
          role="presentation"
          onMouseDown={() => {
            if (!candidateBusy) setDecisionCandidate(null);
          }}
        >
          <section
            className="decision-candidate-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="decision-candidate-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
"""
if old_open in text:
    text = text.replace(old_open, new_open, 1)
elif 'className="decision-candidate-modal"' not in text:
    raise SystemExit("Decision Candidate panel marker not found")

text = text.replace(
    '<span className="eyebrow">Decision Draft</span><h2>决策草案</h2>',
    '<span className="eyebrow">Decision Draft</span><h2 id="decision-candidate-title">决策草案</h2>',
    1,
)

old_close = """          </div>
        </section>
      )}

      <footer className={messageType === 'error' ? 'error-message' : ''}>
"""
new_close = """          </div>
          </section>
        </div>
      )}

      <footer className={messageType === 'error' ? 'error-message' : ''}>
"""
if old_close in text:
    text = text.replace(old_close, new_close, 1)
elif 'className="decision-modal-backdrop"' not in text:
    raise SystemExit("Decision Candidate closing marker not found")

front.write_text(text, encoding="utf-8")
print("patched:", front)

print("Sprint 3-1.1 patch applied.")
