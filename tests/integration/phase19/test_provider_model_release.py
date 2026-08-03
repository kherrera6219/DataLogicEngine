"""Batch 11 provider-owned model release-preparation proofs."""

from __future__ import annotations

import json

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.llm_gateway.model_lifecycle import (
    ProviderModelLifecycleError,
    ProviderModelLifecycleService,
)


def _service(tmp_path, *, coordinator=None):
    model_root = tmp_path / "models"
    model_root.mkdir()
    artifact = model_root / "qualified.onnx"
    artifact.write_bytes(b"bounded-model-artifact")
    service = ProviderModelLifecycleService(
        dataset_root=tmp_path / "datasets",
        admission_root=tmp_path / "training-admissions",
        model_root=model_root,
        release_root=tmp_path / "release-preparations",
        coordinator=coordinator,
    )
    return service, artifact


def _submit(service: ProviderModelLifecycleService, **overrides):
    payload = {
        "artifact_name": "qualified.onnx",
        "current_version": "v1.2.3",
        "increment": "patch",
        "source_commit": "a" * 40,
        "release_channel": "candidate",
        "target_environment": "staging",
        "parameter_count": 1_000_000,
        "target_sparsity": 0.2,
        "pruning_method": "magnitude_unstructured",
        "importance_profile_sha256": "b" * 64,
        "source_bit_depth": 32,
        "target_bit_depth": 8,
        "target_format": "onnx",
        "calibration_profile_sha256": "c" * 64,
        "experiment_id": "release-candidate-v1-2-4",
        "traffic_split_percent": {"control": 90, "candidate": 10},
        "experiment_observations": {},
        "min_sample_size": 1_000,
        "health_observation": {
            "sample_count": 10_000,
            "failure_count": 5,
            "p95_latency_ms": 180.0,
            "maximum_failure_rate": 0.01,
            "maximum_p95_latency_ms": 500.0,
        },
        "idempotency_key": "release-preparation-1",
        "request_id": "batch-11-release",
        "principal_id": "owner-1",
    }
    payload.update(overrides)
    return service.submit_release_preparation(**payload)


def _assert_trace(record: dict, canonical_id: str) -> None:
    states = record["lifecycle"]["trace_states"][canonical_id]
    assert states[:2] == ["planned", "candidate"]
    assert "selected" in states
    assert "executed" in states
    if canonical_id in {"KA-087", "KA-088", "KA-089", "KA-090"}:
        assert "dependency" in states
    if canonical_id == "KA-083":
        assert states[-1] == "effect_proposed"


def test_release_preparation_records_only_owner_admission(tmp_path):
    service, _artifact = _service(tmp_path)

    first = _submit(service)
    second = _submit(service)

    assert first == second
    assert first["status"] == "RELEASE_PREPARATION_RECORDED"
    assert first["proposed_version"] == "v1.2.4"
    assert first["deployment_execution_available"] is False
    assert first["deployment_started"] is False
    assert first["model_registry_write_applied"] is False
    assert first["experiment_activated"] is False
    assert first["traffic_routing_applied"] is False
    assert first["pruning_applied"] is False
    assert first["quantization_applied"] is False
    assert first["provider_calls_applied"] == 0
    assert first["model_artifact_created"] is False
    assert first["lifecycle"]["execution_order"] == [
        ["KA-087", "KA-088", "KA-089", "KA-090"],
        ["KA-083"],
    ]
    receipt = first["authoritative_effect_receipt"]
    assert receipt["operation"] == "record_model_release_preparation"
    assert receipt["ka_proposal_ids"] == [first["deployment_proposal_id"]]
    _assert_trace(first, "KA-083")


def test_release_preparation_preserves_bounded_dependency_proposals(tmp_path):
    service, _artifact = _service(tmp_path)

    record = _submit(service)

    assert record["version_proposal"]["registry_write_applied"] is False
    assert record["experiment_proposal"]["analysis_status"] == (
        "MEASUREMENT_REQUIRED"
    )
    assert record["experiment_proposal"]["routing_applied"] is False
    assert record["pruning_proposal"]["planned_parameter_removal"] == 200_000
    assert record["pruning_proposal"]["pruning_applied"] is False
    assert record["quantization_proposal"][
        "actual_size_measurement_required"
    ] is True
    assert record["quantization_proposal"]["quantization_applied"] is False
    for canonical_id in ("KA-087", "KA-088", "KA-089", "KA-090"):
        assert len(record["dependency_plan_sha256"][canonical_id]) == 64
        _assert_trace(record, canonical_id)


def test_release_preparation_blocks_unhealthy_measurement_without_write(tmp_path):
    service, _artifact = _service(tmp_path)

    with pytest.raises(
        ProviderModelLifecycleError,
        match="health blocks",
    ):
        _submit(
            service,
            health_observation={
                "sample_count": 100,
                "failure_count": 10,
                "p95_latency_ms": 700.0,
                "maximum_failure_rate": 0.01,
                "maximum_p95_latency_ms": 500.0,
            },
        )

    assert not service.release_root.exists()


def test_release_preparation_rejects_path_escape_without_write(tmp_path):
    service, artifact = _service(tmp_path)
    outside = tmp_path / "outside.onnx"
    outside.write_bytes(artifact.read_bytes())

    with pytest.raises(
        ProviderModelLifecycleError,
        match="app-owned file name",
    ):
        _submit(service, artifact_name="../outside.onnx")

    assert not service.release_root.exists()


def test_release_preparation_rejects_idempotency_reuse(tmp_path):
    service, _artifact = _service(tmp_path)
    original = _submit(service)
    target = service.release_root / f"{original['preparation_id']}.json"
    original_bytes = target.read_bytes()

    with pytest.raises(
        ProviderModelLifecycleError,
        match="different release request",
    ):
        _submit(service, target_environment="production")

    assert target.read_bytes() == original_bytes


def test_release_preparation_rejects_tampered_existing_receipt(tmp_path):
    service, _artifact = _service(tmp_path)
    original = _submit(service)
    target = service.release_root / f"{original['preparation_id']}.json"
    tampered = json.loads(target.read_text(encoding="utf-8"))
    tampered["deployment_started"] = True
    target.write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(
        ProviderModelLifecycleError,
        match="failed integrity validation",
    ):
        _submit(service)


def test_release_preparation_rejects_tampered_ka_claim_before_write(tmp_path):
    class TamperedCoordinator(ExtendedSubsystemCoordinator):
        def execute_operation_sync(self, **kwargs):
            execution = super().execute_operation_sync(**kwargs)
            if "KA-083" in execution.results:
                execution.results["KA-083"]["output"][
                    "deployment_applied"
                ] = True
            return execution

    coordinator = TamperedCoordinator()
    service, _artifact = _service(tmp_path, coordinator=coordinator)

    with pytest.raises(
        ProviderModelLifecycleError,
        match="unsupported effect claim",
    ):
        _submit(service)

    assert not service.release_root.exists()
