"""MCP sampling adapter.

Sampling is not advertised by the production MCP surface. It is accepted only
when an application-owned approved provider adapter is explicitly injected; a
missing provider fails closed instead of fabricating a local completion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from flask import current_app, has_app_context
from werkzeug.local import LocalProxy

from core.mcp.mcp_protocol import MCPError, MCPErrorCode


class MCPSamplingService:
    """Use an explicitly injected governed provider or reject sampling."""

    def __init__(self, provider: Any | None = None):
        self.provider = provider

    async def create_message(self, params: dict[str, Any]) -> dict[str, Any]:
        messages = params.get("messages") if isinstance(params.get("messages"), list) else []
        prompt = self._prompt_from_messages(messages)
        model_preferences = params.get("modelPreferences") if isinstance(params.get("modelPreferences"), dict) else {}
        model = model_preferences.get("model") or params.get("model")

        if not self.provider:
            raise MCPError(
                MCPErrorCode.METHOD_NOT_FOUND,
                "Sampling is not enabled",
                data={"reason": "MCP_SAMPLING_DISABLED"},
            )
        if not model:
            raise MCPError(
                MCPErrorCode.INVALID_PARAMS,
                "An approved model is required",
                data={"reason": "MCP_SAMPLING_MODEL_REQUIRED"},
            )
        completion = await self._call_provider(prompt, model=model, params=params)

        return {
            "role": "assistant",
            "content": {
                "type": "text",
                "text": completion,
            },
            "model": model,
            "stopReason": "endTurn",
            "metadata": {
                "provider": "governed",
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
        raise MCPError(
            MCPErrorCode.INTERNAL_ERROR,
            "Configured sampling provider is invalid",
            data={"reason": "MCP_SAMPLING_PROVIDER_INVALID"},
        )


_fallback_sampling_service: MCPSamplingService | None = None


def get_sampling_service() -> MCPSamplingService:
    if has_app_context():
        service = current_app.extensions.get("dle_mcp_sampling_service")
        if service is None:
            service = MCPSamplingService()
            current_app.extensions["dle_mcp_sampling_service"] = service
        return service
    global _fallback_sampling_service
    if _fallback_sampling_service is None:
        _fallback_sampling_service = MCPSamplingService()
    return _fallback_sampling_service


sampling_service = LocalProxy(get_sampling_service)
