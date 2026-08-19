from __future__ import annotations

import asyncio
from types import SimpleNamespace

from scripts import validate_provider_refresh_acceptance as validator


class _FakeAdapter:
    def __init__(self, response_text: str = "ONLINE") -> None:
        self.response_text = response_text
        self.closed = False

    async def complete(self, **kwargs):
        return SimpleNamespace(
            text=self.response_text,
            model=kwargs["model"],
            usage={"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        )

    async def close(self) -> None:
        self.closed = True


def test_openai_case_records_high_reasoning_without_content_or_key(monkeypatch):
    adapter = _FakeAdapter()
    monkeypatch.setattr(validator, "_build_adapter", lambda *_args: adapter)

    result = asyncio.run(
        validator._run_case(
            provider="openai",
            model="gpt-5.6-sol",
            api_key="never-record-this-key",
            credential_source="existing_local_environment",
            timeout_seconds=1,
            max_tokens=256,
        )
    )

    serialized = str(result)
    assert result["status"] == "pass"
    assert result["reasoning_effort"] == "high"
    assert result["response_model"] == "gpt-5.6-sol"
    assert result["credential_or_response_content_recorded"] is False
    assert "never-record-this-key" not in serialized
    assert "ONLINE" not in serialized
    assert adapter.closed is True


def test_credential_lookup_reports_presence_without_returning_it_in_metadata(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "google-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")

    google_key, google_source = validator._credential_for_provider("google")
    openai_key, openai_source = validator._credential_for_provider("openai")

    assert google_key == "google-secret"
    assert openai_key == "openai-secret"
    assert google_source == "existing_local_environment"
    assert openai_source == "existing_local_environment"
