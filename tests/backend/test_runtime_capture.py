"""Focused tests for governed runtime training-data capture."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.dataset_exporter.exporter_core import DatasetExporter
from backend.dataset_exporter.runtime_capture import (
    RuntimeCaptureLoadError,
    RuntimeCaptureStorageError,
    build_capture_row,
    capture_stats,
    is_release_authorized_for_capture,
    load_staged_capture_traces,
    maybe_stage_released_trace,
    purge_staged_capture_runs,
)


def _released_trace(**overrides) -> dict:
    payload = {
        "run_id": "00000000-0000-0000-0000-000000000101",
        "query": "What is the approved release answer?",
        "released_answer": "A released high-confidence answer.",
        "confidence": 0.99,
        "release_authorized": True,
        "status": "completed",
        "truthgate_decision": "allow",
        "tier": "4",
        "stages": [{"stage": "L10_Release", "status": "completed"}],
    }
    payload.update(overrides)
    return payload


def test_flag_off_does_not_write(tmp_path: Path):
    with patch(
        "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
        return_value=False,
    ):
        result = maybe_stage_released_trace(_released_trace(), base_dir=tmp_path)

    assert result["status"] == "skipped"
    assert result["reason"] == "flag_off"
    assert list(tmp_path.glob("**/*.jsonl")) == []


def test_released_trace_is_staged_and_redacted(tmp_path: Path):
    secret_trace = _released_trace(
        released_answer="Contact user@example.com with sk-1234567890abcdef1234567890abcdef."
    )
    with patch(
        "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
        return_value=True,
    ):
        result = maybe_stage_released_trace(secret_trace, base_dir=tmp_path)

    assert result["status"] == "staged"
    staged = Path(result["path"])
    row = json.loads(staged.read_text(encoding="utf-8"))
    assert row["release_authorized"] is True
    assert row["source"] == "runtime_capture"
    assert "sk-1234567890abcdef1234567890abcdef" not in row["released_answer"]
    assert "user@example.com" not in row["released_answer"]
    assert "[REDACTED_SECRET]" in row["released_answer"]


def test_quarantine_and_never_persist_are_skipped(tmp_path: Path):
    with patch(
        "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
        return_value=True,
    ):
        quarantined = maybe_stage_released_trace(
            _released_trace(quarantine=True),
            base_dir=tmp_path,
        )
        never_persist = maybe_stage_released_trace(
            _released_trace(containment_class="never_persist"),
            base_dir=tmp_path,
        )

    assert quarantined["status"] == "skipped"
    assert never_persist["status"] == "skipped"
    assert list(tmp_path.glob("**/*.jsonl")) == []


def test_idempotent_staging(tmp_path: Path):
    with patch(
        "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
        return_value=True,
    ):
        first = maybe_stage_released_trace(_released_trace(), base_dir=tmp_path)
        second = maybe_stage_released_trace(_released_trace(), base_dir=tmp_path)

    assert first["status"] == "staged"
    assert second["status"] == "idempotent"
    assert len(list((tmp_path / "capture").glob("*.jsonl"))) == 1


def test_capture_write_failure_is_non_blocking(tmp_path: Path):
    with (
        patch(
            "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
            return_value=True,
        ),
        patch(
            "backend.dataset_exporter.runtime_capture.PrivacyRedactor.validate_safe_path",
            side_effect=OSError("disk full"),
        ),
    ):
        result = maybe_stage_released_trace(_released_trace(), base_dir=tmp_path)

    assert result["status"] == "error"
    assert result["reason"] == "capture_failed"


def test_capture_stats_failure_is_not_reported_as_zero(tmp_path: Path):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    with patch.object(Path, "glob", side_effect=OSError("secret-volume-path")):
        with pytest.raises(
            RuntimeCaptureStorageError,
            match="runtime_capture_stats_unavailable",
        ) as raised:
            capture_stats(tmp_path)

    assert "secret-volume-path" not in str(raised.value)


def test_malformed_capture_blocks_partial_export(tmp_path: Path):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    (capture_dir / "broken.jsonl").write_text("{not-json", encoding="utf-8")

    with pytest.raises(
        RuntimeCaptureLoadError,
        match="runtime_capture_load_failed",
    ):
        load_staged_capture_traces(base_dir=tmp_path)


def test_retention_purge_removes_only_selected_capture(tmp_path: Path):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    first_run = "00000000-0000-0000-0000-000000000101"
    second_run = "00000000-0000-0000-0000-000000000102"
    first = capture_dir / f"{first_run}.jsonl"
    second = capture_dir / f"{second_run}.jsonl"
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")

    assert purge_staged_capture_runs([first_run], base_dir=tmp_path, dry_run=True) == 1
    assert first.exists()
    assert purge_staged_capture_runs([first_run], base_dir=tmp_path) == 1
    assert not first.exists()
    assert second.exists()


def test_unexpected_capture_failure_propagates_to_post_commit_boundary(tmp_path: Path):
    with (
        patch(
            "backend.dataset_exporter.runtime_capture.is_training_data_capture_enabled",
            return_value=True,
        ),
        patch(
            "backend.dataset_exporter.runtime_capture.build_capture_row",
            side_effect=RuntimeError("unexpected-capture-bug"),
        ),
    ):
        with pytest.raises(RuntimeError, match="unexpected-capture-bug"):
            maybe_stage_released_trace(_released_trace(), base_dir=tmp_path)


def test_export_from_capture_reapplies_gates(tmp_path: Path):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    (capture_dir / "good.jsonl").write_text(
        json.dumps(_released_trace()) + "\n",
        encoding="utf-8",
    )
    (capture_dir / "bad.jsonl").write_text(
        json.dumps(_released_trace(quarantine=True, run_id="bad")) + "\n",
        encoding="utf-8",
    )
    (capture_dir / "low.jsonl").write_text(
        json.dumps(_released_trace(confidence=0.5, run_id="low")) + "\n",
        encoding="utf-8",
    )

    result = DatasetExporter.export_from_capture(
        export_type="sft",
        output_path="from-capture.jsonl",
        min_confidence=0.98,
        format_type="jsonl",
        base_dir=tmp_path,
    )
    assert result["exported_rows"] == 1


def test_build_row_rejects_incomplete_release_evidence():
    assert is_release_authorized_for_capture(_released_trace(release_authorized=False)) is False
    assert build_capture_row(_released_trace(released_answer="")) is None


def test_payload_from_run_uses_snapshot_containment():
    from backend.dataset_exporter.runtime_capture import capture_payload_from_run

    record = SimpleNamespace(
        run_id="00000000-0000-0000-0000-000000000201",
        input_message="query",
        final_answer="answer",
        confidence=0.99,
        tier="4",
        status="completed",
        truthgate_decision="allow",
        regulatory_pass=True,
        security_pass=True,
        data_snapshot={"containment_class": "never_persist", "quarantine": False},
    )
    payload = capture_payload_from_run(record, [])
    assert payload["containment_class"] == "never_persist"
    assert payload["release_authorized"] is True
    assert build_capture_row(payload) is None
