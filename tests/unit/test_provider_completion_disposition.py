"""Provider completion metadata must survive normalization without false success."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.llm_gateway.completion import CompletionDisposition
from backend.llm_gateway.providers.google import GoogleProvider
from backend.llm_gateway.providers.openai import OpenAIProvider


@pytest.mark.parametrize(
    ("native_reason", "expected"),
    [
        ("STOP", CompletionDisposition.COMPLETE),
        ("MAX_TOKENS", CompletionDisposition.LENGTH_LIMITED),
        ("SAFETY", CompletionDisposition.SAFETY_BLOCKED),
        ("OTHER", CompletionDisposition.PROVIDER_INCOMPLETE),
    ],
)
def test_google_finish_reason_maps_to_shared_disposition(native_reason, expected):
    response = SimpleNamespace(
        response_id="google-response-1",
        candidates=[SimpleNamespace(finish_reason=native_reason)],
        prompt_feedback=None,
    )

    completion = GoogleProvider._completion_metadata(response)

    assert completion.disposition is expected
    assert completion.native_reason == native_reason
    assert completion.response_id == "google-response-1"


def test_google_prompt_block_is_not_reported_as_completed():
    response = SimpleNamespace(
        response_id=None,
        candidates=[],
        prompt_feedback=SimpleNamespace(block_reason="PROHIBITED_CONTENT"),
    )

    completion = GoogleProvider._completion_metadata(response)

    assert completion.disposition is CompletionDisposition.SAFETY_BLOCKED
    assert completion.native_reason == "PROHIBITED_CONTENT"


@pytest.mark.parametrize(
    ("status", "reason", "expected"),
    [
        ("completed", None, CompletionDisposition.COMPLETE),
        ("incomplete", "max_output_tokens", CompletionDisposition.LENGTH_LIMITED),
        ("incomplete", "content_filter", CompletionDisposition.SAFETY_BLOCKED),
        ("incomplete", "other", CompletionDisposition.PROVIDER_INCOMPLETE),
        ("failed", "server_error", CompletionDisposition.FAILED),
    ],
)
def test_openai_status_maps_to_shared_disposition(status, reason, expected):
    response = SimpleNamespace(
        id="openai-response-1",
        status=status,
        incomplete_details=(SimpleNamespace(reason=reason) if reason else None),
        error=(SimpleNamespace(code=reason) if status == "failed" else None),
        output=[],
    )

    completion = OpenAIProvider._completion_metadata(response)

    assert completion.disposition is expected
    assert completion.response_id == "openai-response-1"


def test_missing_provider_reason_remains_incomplete_instead_of_assuming_stop():
    google = GoogleProvider._completion_metadata(
        SimpleNamespace(response_id=None, candidates=[], prompt_feedback=None)
    )
    openai = OpenAIProvider._completion_metadata(
        SimpleNamespace(
            id=None,
            status=None,
            incomplete_details=None,
            error=None,
            output=[],
        )
    )

    assert google.disposition is CompletionDisposition.PROVIDER_INCOMPLETE
    assert openai.disposition is CompletionDisposition.PROVIDER_INCOMPLETE

