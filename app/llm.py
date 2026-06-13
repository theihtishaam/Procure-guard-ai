from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import Settings


class LLMError(RuntimeError):
    pass


class AIMLAPIClient:
    def __init__(self, settings: Settings, *, force_disabled: bool = False):
        self.settings = settings
        self.force_disabled = force_disabled

    @property
    def enabled(self) -> bool:
        return bool(not self.force_disabled and self.settings.enable_live_llm and self.settings.aimlapi_api_key)

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise LLMError("AIMLAPI is not configured or live LLM calls are disabled.")

        payload = {
            "model": model or self.settings.aimlapi_model_primary,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.aimlapi_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.aimlapi_base_url}/chat/completions"
        timeout = httpx.Timeout(self.settings.aimlapi_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                raise LLMError(f"AIMLAPI request failed: {exc.__class__.__name__}.") from exc
        if response.status_code >= 400:
            raise LLMError(f"AIMLAPI request failed with status {response.status_code}.")
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return parse_json_object(content)


def parse_json_object(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise LLMError("Model did not return a JSON object.")
    return json.loads(match.group(0))
