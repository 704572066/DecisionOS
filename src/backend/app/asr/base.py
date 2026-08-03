from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(slots=True)
class TranscriptEvent:
    event_type: str
    text: str = ""
    is_final: bool = False
    confidence: float | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    provider: str = "unknown"

    def as_message(self) -> dict:
        return {
            "type": self.event_type,
            "text": self.text,
            "isFinal": self.is_final,
            "confidence": self.confidence,
            "startMs": self.start_ms,
            "endMs": self.end_ms,
            "provider": self.provider,
        }


class StreamingAsrProvider(ABC):
    @abstractmethod
    async def connect(self, *, mime_type: str, language: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_audio(self, audio: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def events(self) -> AsyncIterator[TranscriptEvent]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
