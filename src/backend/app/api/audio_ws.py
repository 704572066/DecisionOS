from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.factory import create_streaming_provider
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import Meeting
from app.observability.runtime_metrics import runtime_metrics
from app.services.reminder_service import realtime_reminder_coordinator
from app.services.transcript_service import append_final_segment

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_json_safe(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (RuntimeError, WebSocketDisconnect):
        return False


async def persist_and_notify(
    websocket: WebSocket,
    *,
    meeting_id: str,
    text: str,
    provider: str,
    confidence: float | None = None,
    start_ms: int | None = None,
    end_ms: int | None = None,
) -> None:
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            await send_json_safe(
                websocket,
                {"type": "error", "message": "Meeting not found"},
            )
            return

        append_result = append_final_segment(
            db,
            meeting=meeting,
            text=text,
            provider=provider,
            confidence=confidence,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        segment = append_result.segment

        await send_json_safe(
            websocket,
            {
                "type": "transcript.saved",
                "created": append_result.created,
                "replacedSegmentId": append_result.replaced_segment_id,
                "segment": {
                    "id": segment.id,
                    "sequence": segment.sequence,
                    "text": segment.text,
                    "provider": segment.asr_provider,
                },
            },
        )

        # Exact duplicates do not need another reminder analysis.
        if not append_result.created and append_result.replaced_segment_id is None:
            return

        result = realtime_reminder_coordinator.analyze_if_due(db, meeting)
        if result and result["reminders"]:
            await send_json_safe(
                websocket,
                {
                    "type": "reminder.batch",
                    "topics": result["topics"],
                    "reminders": result["reminders"],
                },
            )
    finally:
        db.close()


async def receive_init(websocket: WebSocket) -> dict | None:
    try:
        init_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        return json.loads(init_raw)
    except asyncio.TimeoutError:
        await send_json_safe(
            websocket,
            {"type": "error", "message": "语音连接初始化超时"},
        )
    except json.JSONDecodeError:
        await send_json_safe(
            websocket,
            {"type": "error", "message": "缺少合法的初始化消息"},
        )
    return None


@router.websocket("/api/meetings/{meeting_id}/audio-stream")
async def meeting_audio_stream(websocket: WebSocket, meeting_id: str) -> None:
    await websocket.accept()
    runtime_metrics.websocket_opened(meeting_id)

    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
    finally:
        db.close()

    if meeting is None:
        await send_json_safe(
            websocket,
            {"type": "error", "message": "Meeting not found"},
        )
        with suppress(RuntimeError):
            await websocket.close(code=4404)
        return

    init = await receive_init(websocket)
    if init is None:
        with suppress(RuntimeError):
            await websocket.close(code=4400)
        return

    mode = str(init.get("mode") or settings.asr_provider).lower()
    language = str(init.get("language") or settings.asr_language)
    mime_type = str(init.get("mimeType") or "audio/webm")

    await send_json_safe(
        websocket,
        {
            "type": "asr.ready",
            "mode": mode,
            "language": language,
            "mimeType": mime_type,
        },
    )

    if mode == "browser":
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                text_payload = message.get("text")
                if not text_payload:
                    continue

                try:
                    payload = json.loads(text_payload)
                except json.JSONDecodeError:
                    await send_json_safe(
                        websocket,
                        {"type": "error", "message": "收到无效的语音事件"},
                    )
                    continue

                event_type = payload.get("type")
                if event_type == "transcript.partial":
                    await send_json_safe(websocket, payload)
                elif event_type == "transcript.final":
                    text = str(payload.get("text") or "").strip()
                    if text:
                        await send_json_safe(websocket, payload)
                        await persist_and_notify(
                            websocket,
                            meeting_id=meeting_id,
                            text=text,
                            provider="browser",
                            confidence=payload.get("confidence"),
                        )
                elif event_type == "session.ping":
                    await send_json_safe(websocket, {"type": "session.pong"})
                elif event_type == "session.stop":
                    break
        except WebSocketDisconnect:
            logger.info("Browser ASR disconnected: meeting=%s", meeting_id)
        except Exception:
            runtime_metrics.record_error(
                category="websocket.browser_asr",
                message="Browser ASR session failed",
                meeting_id=meeting_id,
            )
            logger.exception("Browser ASR session failed: meeting=%s", meeting_id)
        finally:
            runtime_metrics.websocket_closed(meeting_id)
            with suppress(RuntimeError):
                await websocket.close()
        return

    provider = None
    browser_task: asyncio.Task | None = None
    provider_task: asyncio.Task | None = None
    try:
        provider = create_streaming_provider(mode)
        await provider.connect(mime_type=mime_type, language=language)

        async def receive_browser_audio() -> None:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                audio = message.get("bytes")
                if audio:
                    await provider.send_audio(audio)
                    continue

                text_payload = message.get("text")
                if not text_payload:
                    continue
                payload = json.loads(text_payload)
                if payload.get("type") == "session.stop":
                    break
                if payload.get("type") == "session.ping":
                    await send_json_safe(websocket, {"type": "session.pong"})

        async def receive_asr_events() -> None:
            async for event in provider.events():
                await send_json_safe(websocket, event.as_message())
                if event.is_final and event.text:
                    await persist_and_notify(
                        websocket,
                        meeting_id=meeting_id,
                        text=event.text,
                        provider=event.provider,
                        confidence=event.confidence,
                        start_ms=event.start_ms,
                        end_ms=event.end_ms,
                    )

        browser_task = asyncio.create_task(receive_browser_audio())
        provider_task = asyncio.create_task(receive_asr_events())

        done, pending = await asyncio.wait(
            {browser_task, provider_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            with suppress(WebSocketDisconnect, asyncio.CancelledError):
                task.result()
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    except WebSocketDisconnect:
        logger.info("Streaming ASR disconnected: meeting=%s", meeting_id)
    except Exception as exc:
        runtime_metrics.record_error(
            category="websocket.streaming_asr",
            message=str(exc),
            meeting_id=meeting_id,
        )
        logger.exception("Streaming ASR failed: meeting=%s", meeting_id)
        await send_json_safe(
            websocket,
            {"type": "error", "message": f"ASR 会话异常：{exc}"},
        )
    finally:
        runtime_metrics.websocket_closed(meeting_id)
        for task in (browser_task, provider_task):
            if task and not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        if provider is not None:
            with suppress(Exception):
                await provider.close()
        with suppress(RuntimeError):
            await websocket.close()
