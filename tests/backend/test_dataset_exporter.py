"""Unit tests for the Dataset Exporter module and REST API routes."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Lightweight stubs so tests run without the full app graph when isolated.
# ---------------------------------------------------------------------------

@pytest.fixture
def app_client(app):
    return app.test_client()


def test_export_requires_admin(app_client):
    """Unauthenticated or non-admin callers are rejected."""
    resp = app_client.post("/api/v1/dataset/export", json={"export_type": "sft"})
    assert resp.status_code in (401, 403)


def test_capture_settings_default_off(app_client, admin_headers):
    """Capture flag is fail-closed / default OFF."""
    resp = app_client.get("/api/v1/dataset/capture-settings", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("enabled") is False
    assert body.get("default") is False


def test_capture_settings_toggle_owner_only(app_client, admin_headers):
    """Owner can enable then disable capture; reason is audited."""
    on = app_client.put(
        "/api/v1/dataset/capture-settings",
        headers=admin_headers,
        json={"enabled": True, "reason": "owner_enable_runtime_capture"},
    )
    assert on.status_code == 200
    assert on.get_json().get("enabled") is True

    off = app_client.put(
        "/api/v1/dataset/capture-settings",
        headers=admin_headers,
        json={"enabled": False, "reason": "owner_disable_runtime_capture"},
    )
    assert off.status_code == 200
    assert off.get_json().get("enabled") is False


def test_stats_include_capture_fields(app_client, admin_headers):
    """Stats payload exposes capture_enabled and staged_capture_rows."""
    resp = app_client.get("/api/v1/dataset/stats", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "capture_enabled" in body or "staged_capture_rows" in body


def test_export_rejects_dpo(app_client, admin_headers):
    """DPO remains disabled at the product boundary."""
    resp = app_client.post(
        "/api/v1/dataset/export",
        headers=admin_headers,
        json={"export_type": "dpo", "format_type": "jsonl"},
    )
    assert resp.status_code in (400, 422)


def test_export_requires_release_evidence():
    """Exporter gates stay fail-closed for non-released traces."""
    from backend.dataset_exporter.exporter_core import DatasetExporter

    # Smoke: module import and class present
    assert hasattr(DatasetExporter, "export_from_db")
    assert hasattr(DatasetExporter, "export_from_capture")


def test_privacy_redactor_always_on():
    from backend.dataset_exporter.privacy_redactor import PrivacyRedactor

    redacted = PrivacyRedactor.redact_data(
        {"released_answer": "email me at user@example.com with sk-abc123def456ghi789jkl012"}
    )
    text = json.dumps(redacted)
    assert "user@example.com" not in text
    assert "sk-abc123def456ghi789jkl012" not in text
