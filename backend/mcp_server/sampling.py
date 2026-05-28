"""MCP sampling/createMessage support for local and configured providers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class MCPSamplingService:
    """Create deterministic local completions unless an external provider is supplied."""

    def __init__(self, provider: Any | None = None):
        self.provider = provider

    async def create_message(self, params: dict[str, Any]) -> dict[str, Any]:
        messages = params.get("messages") if isinstance(params.get("messages"), list) else []
        prompt = self._prompt_from_messages(messages)
        model_preferences = params.get("modelPreferences") if isinstance(params.get("modelPreferences"), dict) else {}
        model = model_preferences.get("model") or params.get("model") or "local-deterministic"

        if self.provider:
            completion = await self._call_provider(prompt, model=model, params=params)
        else:
            completion = self._local_completion(prompt)

        return {
            "role": "assistant",
            "content": {
                "type": "text",
                "text": completion,
            },
            "model": model,
            "stopReason": "endTurn",
            "metadata": {
                "provider": "external" if self.provider else "local",
                "created_at": datetime.now(UTC).isoformat(),
            },
        }

    @staticmethod
    def _prompt_from_messages(messages: list[Any]) -> str:
        parts = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, dict):
                parts.append(str(content.get("text") or ""))
            elif isinstance(content, str):
                parts.append(content)
        return "\n".join(part for part in parts if part).strip()

    @staticmethod
    def _local_completion(prompt: str) -> str:
        if not prompt:
            return "No prompt content was supplied."
        return f"Local MCP sampling response: {prompt[:500]}"

    async def _call_provider(self, prompt: str, *, model: str, params: dict[str, Any]) -> str:
        if hasattr(self.provider, "complete"):
            result = self.provider.complete(prompt=prompt, model=model, **params)
            if hasattr(result, "__await__"):
                result = await result
            return str(result)
        if callable(self.provider):
            result = self.provider(prompt)
            if hasattr(result, "__await__"):
                result = await result
            return str(result)
        return self._local_completion(prompt)


sampling_service = MCPSamplingService()
