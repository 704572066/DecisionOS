from __future__ import annotations

import json
import logging
import re
import httpx

from app.core.config import settings
from app.intelligence.models import ReminderEnvelope

logger = logging.getLogger("decisionos.intelligence.llm")


class OpenAICompatibleLLM:
    @property
    def enabled(self) -> bool:
        return bool(
            getattr(settings, "openai_base_url", "")
            and getattr(settings, "openai_api_key", "")
            and getattr(settings, "openai_model", "")
        )

    async def generate_reminders(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> ReminderEnvelope:
        if not self.enabled:
            raise RuntimeError("LLM is not configured")

        base = settings.openai_base_url.rstrip("/")
        timeout = float(getattr(settings, "llm_timeout_seconds", 30.0))
        body = {
            "model": settings.openai_model,
            "temperature": float(getattr(settings, "reminder_temperature", 0.1)),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if getattr(settings, "llm_json_mode", False):
            body["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        content = payload["choices"][0]["message"]["content"]
        data = _parse_json_object(content)
        return ReminderEnvelope.model_validate(data)


def _parse_json_object(content: str) -> dict:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


llm_provider = OpenAICompatibleLLM()
