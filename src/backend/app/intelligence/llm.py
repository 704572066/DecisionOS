from __future__ import annotations
import json
import logging
import re
from collections.abc import AsyncIterator

import httpx

from app.core.config import settings
from app.intelligence.models import ReminderEnvelope
from app.intelligence.streaming import parse_sse_content

logger = logging.getLogger("decisionos.intelligence.llm")

class OpenAICompatibleLLM:
    @property
    def enabled(self) -> bool:
        return bool(
            getattr(settings, "openai_base_url", "")
            and getattr(settings, "openai_api_key", "")
            and getattr(settings, "openai_model", "")
        )

    def _body(self, system_prompt: str, user_prompt: str, *, stream: bool,) -> dict:
        body = {
            "model": settings.openai_model,
            "temperature": float(
                getattr(
                    settings,
                    "reminder_temperature",
                    0.1,
                )
            ),
            "stream": stream,

            "thinking": {
                "type": (
                    "enabled"
                    if getattr(
                        settings,
                        "reminder_enable_thinking",
                        False,
                    )
                    else "disabled"
                )
            },

            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        if getattr(
            settings,
            "llm_json_mode",
            False,
        ):
            body["response_format"] = {
                "type": "json_object"
            }

        return body

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> dict:
        if not self.enabled:
            raise RuntimeError("LLM is not configured")

        body = self._body(system_prompt, user_prompt, stream=False)
        body["temperature"] = temperature

        async with httpx.AsyncClient(
            timeout=float(getattr(settings, "llm_timeout_seconds", 30.0))
        ) as client:
            response = await client.post(
                settings.openai_base_url.rstrip("/") + "/chat/completions",
                headers=self._headers(),
                json=body,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

        return _parse_json_object(content)

    async def generate_reminders(self, system_prompt: str, user_prompt: str) -> ReminderEnvelope:
        if not self.enabled:
            raise RuntimeError("LLM is not configured")
        async with httpx.AsyncClient(timeout=float(getattr(settings, "llm_timeout_seconds", 30.0))) as client:
            response = await client.post(
                settings.openai_base_url.rstrip("/") + "/chat/completions",
                headers=self._headers(),
                json=self._body(system_prompt, user_prompt, stream=False),
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        return ReminderEnvelope.model_validate(_parse_json_object(content))

    async def stream_reminders(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        if not self.enabled:
            raise RuntimeError("LLM is not configured")
        timeout = httpx.Timeout(
            connect=10.0,
            read=float(getattr(settings, "llm_timeout_seconds", 30.0)),
            write=15.0,
            pool=10.0,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                settings.openai_base_url.rstrip("/") + "/chat/completions",
                headers=self._headers(),
                json=self._body(system_prompt, user_prompt, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue
                    try:
                        content = parse_sse_content(line)
                    except Exception:
                        continue
                    if content:
                        yield content

    @staticmethod
    def _headers() -> dict:
        return {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

def parse_final_stream_json(content: str) -> ReminderEnvelope:
    return ReminderEnvelope.model_validate(_parse_json_object(content))

def _parse_json_object(content: str) -> dict:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
        raise

llm_provider = OpenAICompatibleLLM()
