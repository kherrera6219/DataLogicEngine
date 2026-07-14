from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from backend.llm_gateway.provider_manifest import (
    MANIFEST_PATH,
    PROVIDERS,
    SUPPORTED_PROVIDER_TYPES,
    normalize_provider_type,
    validate_provider_model,
)


ROOT = Path(__file__).resolve().parents[2]


def test_manifest_is_only_provider_model_contract() -> None:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert raw["schema_version"] == "provider-manifest.v1"
    assert SUPPORTED_PROVIDER_TYPES == {"openai", "google"}
    assert [provider.id for provider in PROVIDERS] == ["openai", "google"]
    assert all(provider.pricing_status == "unknown" for provider in PROVIDERS)


def test_provider_alias_is_explicit_and_unknown_provider_fails_closed() -> None:
    assert normalize_provider_type("gemini") == "google"
    with pytest.raises(ValueError, match="Unsupported provider"):
        normalize_provider_type("anthropic")
    with pytest.raises(ValueError, match="Unsupported provider"):
        normalize_provider_type(None)


def test_undeclared_model_fails_closed() -> None:
    assert validate_provider_model("openai", None) == "gpt-5.5"
    with pytest.raises(ValueError, match="Unsupported model"):
        validate_provider_model("openai", "gpt-4")


def test_generated_provider_artifacts_are_current() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/generate_provider_manifest.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
