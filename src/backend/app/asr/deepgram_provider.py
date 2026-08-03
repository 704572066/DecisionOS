from __future__ import annotations

import json
from collections.abc import AsyncIterator
from urllib.parse import urlencode

import websockets
from websockets.client import WebSocketClientProtocol

from app.asr.base import StreamingAsrProvider, TranscriptEvent
from app.core.config import settings


class DeepgramStreamingAsrProvider(StreamingAsrProvider):
    def __init__(self) -> None:
        self._socket: WebSocketClientProtocol | None = None

    async def connect(self, *, mime_type: str, language: str) -> None:
        if not settings.deepgram_api_key:
            raise RuntimeError("DEEPGRAM_API_KEY 未配置")

        params = {
            "model": settings.deepgram_model,
            "language": language or settings.asr_language,
            "smart_format": "true",
            "punctuate": "true",
            "interim_results": "true",
            "vad_events": "true",
            "endpointing": str(settings.deepgram_endpointing_ms),
        }
        url = f"wss://api.deepgram.com/v1/listen?{urlencode(params)}"
        self._socket = await websockets.connect(
            url,
            extra_headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": mime_type or "audio/webm",
            },
            ping_interval=20,
            ping_timeout=20,
            max_size=8 * 1024 * 1024,
        )

    async def send_audio(self, audio: bytes) -> None:
        if self._socket is None:
            raise RuntimeError("ASR WebSocket 尚未连接")
        await self._socket.send(audio)

    async def events(self) -> AsyncIterator[TranscriptEvent]:
        if self._socket is None:
            raise RuntimeError("ASR WebSocket 尚未连接")

        async for raw in self._socket:
            if not isinstance(raw, str):
                continue
            payload = json.loads(raw)
            event_type = payload.get("type")

            if event_type == "Results":
                channel = payload.get("channel") or {}
                alternatives = channel.get("alternatives") or []
                if not alternatives:
                    continue
                best = alternatives[0]
                text = (best.get("transcript") or "").strip()
                if not text:
                    continue

                is_final = bool(payload.get("is_final"))
                start = float(payload.get("start") or 0)
                duration = float(payload.get("duration") or 0)
                yield TranscriptEvent(
                    event_type="transcript.final" if is_final else "transcript.partial",
                    text=text,
                    is_final=is_final,
                    confidence=best.get("confidence"),
                    start_ms=int(start * 1000),
                    end_ms=int((start + duration) * 1000),
                    provider="deepgram",
                )
            elif event_type == "UtteranceEnd":
                yield TranscriptEvent(
                    event_type="asr.utterance_end",
                    provider="deepgram",
                )

    async def close(self) -> None:
        if self._socket is None:
            return
        try:
            await self._socket.send(json.dumps({"type": "CloseStream"}))
        finally:
            await self._socket.close()
            self._socket = None
