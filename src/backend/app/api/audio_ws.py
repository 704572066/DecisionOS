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
from app.services.reminder_service import realtime_reminder_coordinator
from app.services.transcript_service import append_final_segment

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_json_safe(websocket: WebSocket, payload: dict) -> None:
    try:
        await websocket.send_json(payload)
    except RuntimeError:
        pass


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
            await send_json_safe(websocket, {"type": "error", "message": "Meeting not found"})
            return

        segment = append_final_segment(
            db,
            meeting=meeting,
            text=text,
            provider=provider,
            confidence=confidence,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        await send_json_safe(
            websocket,
            {
                "type": "transcript.saved",
                "segment": {
                    "id": segment.id,
                    "sequence": segment.sequence,
                    "text": segment.text,
                    "provider": segment.asr_provider,
                },
            },
        )

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


@router.websocket("/api/meetings/{meeting_id}/audio-stream")
async def meeting_audio_stream(websocket: WebSocket, meeting_id: str) -> None:
    await websocket.accept()

    db = SessionLocal()
    meeting = db.get(Meeting, meeting_id)
    db.close()
    if meeting is None:
        await websocket.send_json({"type": "error", "message": "Meeting not found"})
        await websocket.close(code=4404)
        return

    try:
        init_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        init = json.loads(init_raw)
    except (asyncio.TimeoutError, json.JSONDecodeError):
        await websocket.send_json({"type": "error", "message": "缺少合法的初始化消息"})
        await websocket.close(code=4400)
        return

    mode = str(init.get("mode") or settings.asr_provider).lower()
    language = str(init.get("language") or settings.asr_language)
    mime_type = str(init.get("mimeType") or "audio/webm")

    await websocket.send_json(
        {
            "type": "asr.ready",
            "mode": mode,
            "language": language,
            "mimeType": mime_type,
        }
    )

    # Browser mode uses Web Speech API in the frontend. Final text is sent as JSON.
    if mode == "browser":
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                text_payload = message.get("text")
                if not text_payload:
                    continue
                payload = json.loads(text_payload)
                event_type = payload.get("type")
                if event_type == "transcript.partial":
                    await websocket.send_json(payload)
                elif event_type == "transcript.final":
                    text = str(payload.get("text") or "").strip()
                    if text:
                        await websocket.send_json(payload)
                        await persist_and_notify(
                            websocket,
                            meeting_id=meeting_id,
                            text=text,
                            provider="browser",
                            confidence=payload.get("confidence"),
                        )
                elif event_type == "session.stop":
                    break
        except WebSocketDisconnect:
            return
        return

    # Provider mode forwards MediaRecorder binary chunks to a streaming ASR service.
    try:
        provider = create_streaming_provider(mode)
        await provider.connect(mime_type=mime_type, language=language)
    except Exception as exc:
        logger.exception("ASR provider initialization failed")
        await websocket.send_json({"type": "error", "message": f"ASR 初始化失败：{exc}"})
        await websocket.close(code=1011)
        return

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
            if text_payload:
                payload = json.loads(text_payload)
                if payload.get("type") == "session.stop":
                    break

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
    try:
        done, pending = await asyncio.wait(
            {browser_task, provider_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            with suppress(WebSocketDisconnect, asyncio.CancelledError):
                task.result()
        for task in pending:
            task.cancel()
    finally:
        await provider.close()
        with suppress(RuntimeError):
            await websocket.close()
