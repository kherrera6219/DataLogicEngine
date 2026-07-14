"""Governed audio capability boundary.

Phase 7 removes the former direct OpenAI/Google speech calls because they bypassed
the request budget, privacy ledger, cancellation, and provider manifest. Audio
remains explicitly unavailable until a governed, separately disclosed audio
adapter is approved and injected by the application runtime.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import inspect
from typing import Any

from flask import current_app, has_app_context
from werkzeug.local import LocalProxy


class AudioCapabilityUnavailable(RuntimeError):
    """Raised when no approved governed audio adapter is installed."""


Transcriber = Callable[[bytes, str], str | Awaitable[str]]
Synthesizer = Callable[[str, str], bytes | Awaitable[bytes]]


class AudioService:
    """Audio boundary that never creates or owns a provider SDK client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transcriber: Transcriber | None = None,
        synthesizer: Synthesizer | None = None,
    ) -> None:
        # ``api_key`` is retained only for constructor compatibility and is
        # intentionally ignored; credentials belong to the governed gateway.
        del api_key
        self._transcriber = transcriber
        self._synthesizer = synthesizer

    @staticmethod
    async def _resolve(value: Any) -> Any:
        return await value if inspect.isawaitable(value) else value

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        if self._transcriber is None:
            raise AudioCapabilityUnavailable(
                "Audio transcription is unavailable until a governed audio adapter is installed"
            )
        result = await self._resolve(self._transcriber(audio_bytes, filename))
        if not isinstance(result, str) or not result.strip():
            raise AudioCapabilityUnavailable("Governed audio adapter returned no transcript")
        return result

    async def synthesize(self, text: str, voice: str = "alloy") -> bytes:
        if self._synthesizer is None:
            raise AudioCapabilityUnavailable(
                "Speech synthesis is unavailable until a governed audio adapter is installed"
            )
        result = await self._resolve(self._synthesizer(text, voice))
        if not isinstance(result, bytes) or not result:
            raise AudioCapabilityUnavailable("Governed audio adapter returned no audio")
        return result


_fallback_audio_service: AudioService | None = None


def get_audio_service() -> AudioService:
    """Return the audio boundary owned by the active application."""
    if has_app_context():
        service = current_app.extensions.get("dle_audio_service")
        if service is None:
            service = AudioService()
            current_app.extensions["dle_audio_service"] = service
        return service
    global _fallback_audio_service
    if _fallback_audio_service is None:
        _fallback_audio_service = AudioService()
    return _fallback_audio_service


audio_service = LocalProxy(get_audio_service)
