"""OpenAI Responses API adapter using the official asynchronous client."""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from backend.llm_gateway.provider_manifest import validate_provider_model
from backend.llm_gateway.providers.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    provider_type = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError("Missing OPENAI_API_KEY")
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
            timeout=timeout_seconds,
            max_retries=0,
        )

    @staticmethod
    def _request(
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        target_model = validate_provider_model("openai", model)
        output_budget = max(16, int(max_tokens or 0))
        request: dict[str, Any] = {
            "model": target_model,
            "input": messages,
            "max_output_tokens": output_budget,
        }
        if target_model.lower().startswith(("gpt-5", "o1", "o3", "o4")):
            request["reasoning"] = {"effort": "medium"}
        else:
            request["temperature"] = temperature
        return request

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        request = self._request(messages, model, temperature, max_tokens)
        response = await self.client.responses.create(**request)
        text = str(getattr(response, "output_text", "") or "")
        if not text:
            raise ValueError("Malformed provider response: missing output text")
        usage_object = getattr(response, "usage", None)
        usage = {
            "prompt_tokens": int(getattr(usage_object, "input_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage_object, "output_tokens", 0) or 0),
            "total_tokens": int(getattr(usage_object, "total_tokens", 0) or 0),
        }
        return LLMResponse(text=text, raw={"response_id": getattr(response, "id", None)}, model=request["model"], usage=usage)

    async def stream(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        request = self._request(messages, model, temperature, max_tokens)
        stream = await self.client.responses.create(**request, stream=True)
        async for event in stream:
            if getattr(event, "type", "") == "response.output_text.delta":
                delta = str(getattr(event, "delta", "") or "")
                if delta:
                    yield delta

    async def close(self) -> None:
        await self.client.close()
