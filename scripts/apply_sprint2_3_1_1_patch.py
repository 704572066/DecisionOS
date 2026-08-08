#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

config = ROOT / 'src/backend/app/core/config.py'
text = config.read_text(encoding='utf-8')
if 'reminder_enable_thinking:' not in text:
    marker = '    reminder_temperature: float = 0.1\n' if '    reminder_temperature: float = 0.1\n' in text else '    reminder_cooldown_seconds: int = 3\n'
    if marker not in text:
        raise SystemExit('config.py reminder marker not found')
    text = text.replace(marker, marker + '    reminder_enable_thinking: bool = False\n', 1)
    config.write_text(text, encoding='utf-8')
    print('patched:', config)

llm = ROOT / 'src/backend/app/intelligence/llm.py'
text = llm.read_text(encoding='utf-8')
if '"enable_thinking": bool(' not in text:
    marker = '            "stream": stream,\n            "messages": [\n'
    replacement = (
        '            "stream": stream,\n'
        '            "enable_thinking": bool(\n'
        '                getattr(settings, "reminder_enable_thinking", False)\n'
        '            ),\n'
        '            "messages": [\n'
    )
    if marker not in text:
        raise SystemExit('llm.py request body marker not found')
    llm.write_text(text.replace(marker, replacement, 1), encoding='utf-8')
    print('patched:', llm)

audio = ROOT / 'src/backend/app/api/audio_ws.py'
text = audio.read_text(encoding='utf-8')
if 'async def stream_ai_reminder(' not in text:
    raise SystemExit('Sprint 2-3.1 stream_ai_reminder() not found; merge Sprint 2-3.1 first')
if 'import time\n' not in text:
    if 'import logging\n' not in text:
        raise SystemExit('audio_ws.py logging import marker not found')
    text = text.replace('import logging\n', 'import logging\nimport time\n', 1)

old = '''        parser = StructuredReminderStreamParser(reminder_id)
        raw = ""

        async for chunk in llm_provider.stream_reminders(system_prompt, user_prompt):
'''
new = '''        parser = StructuredReminderStreamParser(reminder_id)
        raw = ""
        llm_started_at = time.perf_counter()
        first_content_ms = None

        async for chunk in llm_provider.stream_reminders(system_prompt, user_prompt):
            if first_content_ms is None:
                first_content_ms = (time.perf_counter() - llm_started_at) * 1000
                await send_json_safe(websocket, {
                    "type": "reminder.ttft",
                    "reminderId": reminder_id,
                    "firstContentMs": round(first_content_ms, 2),
                })
'''
if 'first_content_ms = None' not in text:
    if old not in text:
        raise SystemExit('audio_ws.py streaming loop marker not found')
    text = text.replace(old, new, 1)

old_completed = '''        await send_json_safe(websocket, {
            "type": "reminder.completed",
            "reminderId": reminder_id,
            "reminders": [item.websocket_dict() for item in validated],
            "context": context.model_dump(mode="json"),
        })
'''
new_completed = '''        llm_total_ms = (time.perf_counter() - llm_started_at) * 1000

        await send_json_safe(websocket, {
            "type": "reminder.completed",
            "reminderId": reminder_id,
            "reminders": [item.websocket_dict() for item in validated],
            "context": context.model_dump(mode="json"),
            "diagnostics": {
                "thinkingEnabled": bool(
                    getattr(settings, "reminder_enable_thinking", False)
                ),
                "firstContentMs": (
                    round(first_content_ms, 2)
                    if first_content_ms is not None else None
                ),
                "llmTotalMs": round(llm_total_ms, 2),
            },
        })
'''
if '"thinkingEnabled": bool(' not in text:
    if old_completed not in text:
        raise SystemExit('audio_ws.py completed marker not found')
    text = text.replace(old_completed, new_completed, 1)

audio.write_text(text, encoding='utf-8')
print('patched:', audio)

frontend = ROOT / 'src/frontend/src/main.tsx'
text = frontend.read_text(encoding='utf-8')
if 'streamingTtftMs' not in text:
    marker = '  const [streamingReminder, setStreamingReminder] = useState<{\n'
    if marker not in text:
        raise SystemExit('Sprint 2-3.1 streamingReminder state not found in frontend')
    text = text.replace(marker, '  const [streamingTtftMs, setStreamingTtftMs] = useState<number | null>(null);\n' + marker, 1)

    old_started = "        case 'reminder.started':\n          setStreamingReminder({\n"
    new_started = "        case 'reminder.started':\n          setStreamingTtftMs(null);\n          setStreamingReminder({\n"
    if old_started not in text:
        raise SystemExit('frontend reminder.started marker not found')
    text = text.replace(old_started, new_started, 1)

    old_delta = "        case 'reminder.delta':\n"
    new_delta = "        case 'reminder.ttft':\n          setStreamingTtftMs(payload.firstContentMs ?? null);\n          break;\n        case 'reminder.delta':\n"
    if old_delta not in text:
        raise SystemExit('frontend reminder.delta marker not found')
    text = text.replace(old_delta, new_delta, 1)

    old_ui = '              <div className="streaming-state">AI 生成中…</div>\n'
    new_ui = '''              <div className="streaming-state">
                AI 生成中…
                {streamingTtftMs !== null && (
                  <span className="streaming-ttft">
                    首字 {Math.round(streamingTtftMs)}ms
                  </span>
                )}
              </div>
'''
    if old_ui not in text:
        raise SystemExit('frontend streaming-state marker not found')
    text = text.replace(old_ui, new_ui, 1)
    frontend.write_text(text, encoding='utf-8')
    print('patched:', frontend)

print('Sprint 2-3.1.1 patch applied.')
