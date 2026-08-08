#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"marker not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

prompt = ROOT / "src/backend/app/intelligence/prompt_builder.py"
text = prompt.read_text(encoding="utf-8")
if "折扣率不等于毛利率" not in text:
    text = text.replace(
        "7. 只返回 JSON，不要 Markdown。",
        "7. 不同业务指标即使数值相同，也不得直接比较或推导。例如：折扣率不等于毛利率，付款周期不等于回款概率。\\n8. 必须按字段顺序输出 JSON：type、title、summary、suggestion、reason、sources、confidence。\\n9. 只返回 JSON，不要 Markdown。"
    )
    prompt.write_text(text, encoding="utf-8")

audio = ROOT / "src/backend/app/api/audio_ws.py"
text = audio.read_text(encoding="utf-8")
if "stream_ai_reminder(" not in text:
    if "from uuid import uuid4" not in text:
        text = text.replace("import asyncio\n", "import asyncio\nfrom uuid import uuid4\n", 1)
    if "from app.intelligence.reminder_engine import ai_reminder_engine" not in text:
        text = text.replace(
            "from app.models.entities import Meeting\n",
            "from app.models.entities import Meeting\nfrom app.intelligence.reminder_engine import ai_reminder_engine\n",
            1,
        )
    text = text.replace(
        "logger = logging.getLogger(__name__)\n",
        "logger = logging.getLogger(__name__)\nstreaming_reminder_tasks: set[asyncio.Task] = set()\n",
        1,
    )

    inserted = '''
async def stream_ai_reminder(websocket: WebSocket, meeting_id: str) -> None:
    from app.context.service import build_meeting_context
    from app.intelligence.llm import llm_provider, parse_final_stream_json
    from app.intelligence.prompt_builder import build_prompt
    from app.intelligence.reranker import rerank_context
    from app.intelligence.streaming import StructuredReminderStreamParser
    from app.retrieval.query_builder import build_retrieval_query
    from app.retrieval.service import hybrid_retriever

    db = SessionLocal()
    reminder_id = "reminder-" + uuid4().hex[:12]
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return

        context = build_meeting_context(db, meeting)
        retrieval = await hybrid_retriever.search(
            db,
            build_retrieval_query(context, top_k=8),
        )
        evidence = rerank_context(context, retrieval["results"], top_k=5)

        await send_json_safe(websocket, {
            "type": "reminder.started",
            "reminderId": reminder_id,
        })

        if not llm_provider.enabled:
            result = await realtime_reminder_coordinator.analyze_if_due(
                db, meeting, force=True
            )
            await send_json_safe(websocket, {
                "type": "reminder.completed",
                "reminderId": reminder_id,
                "reminders": (result or {}).get("reminders", []),
                "diagnostics": (result or {}).get("diagnostics"),
            })
            return

        system_prompt, user_prompt = build_prompt(context, evidence)
        parser = StructuredReminderStreamParser(reminder_id)
        raw = ""

        async for chunk in llm_provider.stream_reminders(system_prompt, user_prompt):
            raw += chunk
            for update in parser.feed(chunk):
                await send_json_safe(websocket, {
                    "type": "reminder.delta",
                    "reminderId": reminder_id,
                    "field": update.field,
                    "delta": update.delta,
                    "accumulated": update.accumulated,
                })

        envelope = parse_final_stream_json(raw)
        validated = ai_reminder_engine._validate_sources(
            envelope.reminders,
            evidence,
        )[:3]

        await send_json_safe(websocket, {
            "type": "reminder.completed",
            "reminderId": reminder_id,
            "reminders": [item.websocket_dict() for item in validated],
            "context": context.model_dump(mode="json"),
        })
    except Exception as exc:
        logger.exception("Streaming AI reminder failed: meeting=%s", meeting_id)
        await send_json_safe(websocket, {
            "type": "reminder.failed",
            "reminderId": reminder_id,
            "message": str(exc),
        })
    finally:
        db.close()

def schedule_streaming_reminder(websocket: WebSocket, meeting_id: str) -> None:
    task = asyncio.create_task(stream_ai_reminder(websocket, meeting_id))
    streaming_reminder_tasks.add(task)
    task.add_done_callback(streaming_reminder_tasks.discard)

'''
    marker = "async def persist_and_notify("
    if marker not in text:
        raise SystemExit("persist_and_notify marker not found")
    text = text.replace(marker, inserted + marker, 1)

    old_blocks = [
'''        result = await realtime_reminder_coordinator.analyze_if_due(db, meeting)
        if result and result["reminders"]:
            await send_json_safe(
                websocket,
                {
                    "type": "reminder.batch",
                    "topics": result["topics"],
                    "reminders": result["reminders"],
                    "context": result.get("context"),
                    "diagnostics": result.get("diagnostics"),
                    "rerankedEvidence": result.get("rerankedEvidence"),
                },
            )
''',
'''        result = await realtime_reminder_coordinator.analyze_if_due(db, meeting)
        if result and result["reminders"]:
            await send_json_safe(
                websocket,
                {
                    "type": "reminder.batch",
                    "topics": result["topics"],
                    "reminders": result["reminders"],
                    "context": result.get("context"),
                },
            )
'''
    ]
    replaced = False
    for old in old_blocks:
        if old in text:
            text = text.replace(old, "        schedule_streaming_reminder(websocket, meeting_id)\n", 1)
            replaced = True
            break
    if not replaced:
        raise SystemExit("existing reminder send block not found")
    audio.write_text(text, encoding="utf-8")

front = ROOT / "src/frontend/src/main.tsx"
text = front.read_text(encoding="utf-8")
if "streamingReminder" not in text:
    marker = "  const [reminders, setReminders] = useState<Reminder[]>([]);\n"
    addition = marker + '''  const [streamingReminder, setStreamingReminder] = useState<{
    id: string;
    title: string;
    summary: string;
    suggestion: string;
    reason: string;
  } | null>(null);
'''
    if marker not in text:
        raise SystemExit("frontend reminder state marker not found")
    text = text.replace(marker, addition, 1)

    case_marker = "        case 'reminder.batch':\n"
    cases = '''        case 'reminder.started':
          setStreamingReminder({
            id: payload.reminderId,
            title: '',
            summary: '',
            suggestion: '',
            reason: '',
          });
          break;
        case 'reminder.delta':
          setStreamingReminder((current) => {
            if (!current || current.id !== payload.reminderId) return current;
            return {...current, [payload.field]: payload.accumulated};
          });
          break;
        case 'reminder.completed':
          setStreamingReminder(null);
          if (payload.reminders) {
            setReminders((current) =>
              [...payload.reminders, ...current].slice(0, 10)
            );
          }
          break;
        case 'reminder.failed':
          setStreamingReminder(null);
          showError(payload.message || 'AI 提醒生成失败');
          break;
'''
    if case_marker not in text:
        raise SystemExit("frontend reminder.batch case not found")
    text = text.replace(case_marker, cases + case_marker, 1)

    panel = "          <h2>AI 实时提醒</h2>\n"
    card = panel + '''          {streamingReminder && (
            <article className="streaming-reminder">
              <div className="streaming-state">AI 生成中…</div>
              {streamingReminder.title && <strong>{streamingReminder.title}</strong>}
              {streamingReminder.summary && <p>{streamingReminder.summary}</p>}
              {streamingReminder.suggestion && (
                <p><strong>建议：</strong>{streamingReminder.suggestion}</p>
              )}
              {streamingReminder.reason && (
                <p><strong>依据：</strong>{streamingReminder.reason}</p>
              )}
            </article>
          )}
'''
    if panel not in text:
        raise SystemExit("frontend AI panel marker not found")
    text = text.replace(panel, card, 1)
    front.write_text(text, encoding="utf-8")

print("Sprint 2-3.1 patch applied.")
