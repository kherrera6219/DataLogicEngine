"""Google Gemini adapter using the official asynchronous client surface."""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from backend.llm_gateway.provider_manifest import validate_provider_model
from backend.llm_gateway.providers.base import LLMProvider, LLMResponse


class GoogleProvider(LLMProvider):
    provider_type = "google"

    def __init__(self, *, api_key: str | None = None, timeout_seconds: float = 30.0) -> None:
        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError("Missing GOOGLE_API_KEY/GEMINI_API_KEY")
        from google import genai
        from google.genai import types

        self.client = genai.Client(
            api_key=resolved_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self.types = types

    def _request(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        system_parts: list[str] = []
        prompt_parts: list[str] = []
        for message in messages:
            role = str(message.get("role") or "user")
            content = str(message.get("content") or "")
            if role == "system":
                system_parts.append(content)
            else:
                prompt_parts.append(f"{role.title()}: {content}")
        return {
            "model": validate_provider_model("google", model),
            "contents": "\n".join(prompt_parts),
            "config": self.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max(1, int(max_tokens or 0)),
                system_instruction="\n\n".join(system_parts) or None,
            ),
        }

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        request = self._request(messages, model, temperature, max_tokens)
        response = await self.client.aio.models.generate_content(**request)
        text = str(getattr(response, "text", "") or "")
        if not text:
            raise ValueError("Malformed provider response: missing output text")
        usage_object = getattr(response, "usage_metadata", None)
        usage = {
            "prompt_tokens": int(getattr(usage_object, "prompt_token_count", 0) or 0),
            "completion_tokens": int(getattr(usage_object, "candidates_token_count", 0) or 0),
            "total_tokens": int(getattr(usage_object, "total_token_count", 0) or 0),
        }
        return LLMResponse(text=text, raw={}, model=request["model"], usage=usage)

    async def stream(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        request = self._request(messages, model, temperature, max_tokens)
        stream = await self.client.aio.models.generate_content_stream(**request)
        async for chunk in stream:
            text = str(getattr(chunk, "text", "") or "")
            if text:
                yield text

    async def close(self) -> None:
        await self.client.aio.aclose()
