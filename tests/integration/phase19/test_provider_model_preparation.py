"""Batch 10 provider-owned model preparation and evaluation proofs."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.llm_gateway.model_lifecycle import (
    ProviderModelLifecycleError,
    ProviderModelLifecycleService,
)


def _dataset(tmp_path):
    dataset_root = tmp_path / "datasets"
    dataset_root.mkdir()
    artifact = dataset_root / "sft-qualified.jsonl"
    artifact.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "question"},
                            {"role": "assistant", "content": "answer"},
                        ],
                        "metadata": {"release_authorized": True},
                    }
                ),
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "second"},
                            {"role": "assistant", "content": "response"},
                        ],
                        "metadata": {"release_authorized": True},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return dataset_root, artifact


def _submit(service: ProviderModelLifecycleService, **overrides):
    payload = {
        "artifact_name": "sft-qualified.jsonl",
        "export_type": "sft",
        "model_name": "local-evaluation-model",
        "epochs": 2,
        "hyperparameters": {},
        "parameter_space": {
            "batch_size": [8, 16],
            "learning_rate": [0.001],
        },
        "tuning_observations": [
            {
                "params": {"batch_size": 16, "learning_rate": 0.001},
                "score": 0.91,
                "sample_count": 200,
            }
        ],
        "idempotency_key": "training-admission-1",
        "request_id": "batch-10-training",
        "principal_id": "owner-1",
    }
    payload.update(overrides)
    return service.submit_training_admission(**payload)


def _assert_owner_trace(job: dict, canonical_id: str) -> None:
    states = job["lifecycle"]["trace_states"][canonical_id]
    assert states[:2] == ["planned", "candidate"]
    assert states[-3:] == ["admitted", "executing", "executed"] or states[
        -4:-1
    ] == ["admitted", "executing", "executed"]
    assert "selected" in states
    if canonical_id in {"KA-085", "KA-086"}:
        assert "dependency" in states
    if canonical_id == "KA-081":
        assert states[-1] == "effect_proposed"


def test_ka_081_owning_path_records_only_an_admission(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    first = _submit(service)
    second = _submit(service)

    assert first == second
    assert first["status"] == "ADMISSION_RECORDED"
    assert first["training_execution_available"] is False
    assert first["training_started"] is False
    assert first["worker_assigned"] is False
    assert first["epochs_run"] == 0
    assert first["checkpoints_created"] == 0
    assert first["model_artifact_created"] is False
    assert first["provider_calls_applied"] == 0
    assert first["lifecycle"]["execution_order"] == [
        ["KA-085", "KA-086"],
        ["KA-081"],
    ]
    receipt = first["authoritative_effect_receipt"]
    assert receipt["status"] == "applied"
    assert receipt["service"] == "ProviderModelLifecycleService"
    assert receipt["operation"] == "record_model_training_admission"
    assert receipt["resource_id"] == first["job_id"]
    assert receipt["ka_proposal_ids"] == [first["training_proposal_id"]]
    assert len(receipt["request_sha256"]) == 64
    assert len(receipt["result_sha256"]) == 64
    _assert_owner_trace(first, "KA-081")


def test_ka_085_owning_path_builds_only_content_free_profile_features(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    job = _submit(service)

    assert job["dataset"]["row_count"] == 2
    assert job["dataset"]["feature_profile_records"] == 2
    assert len(job["feature_plan_sha256"]) == 64
    assert "question" not in json.dumps(job)
    assert "answer" not in json.dumps(job)
    _assert_owner_trace(job, "KA-085")


def test_ka_086_owning_path_consumes_only_measured_tuning_results(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    job = _submit(service)

    assert job["hyperparameters"] == {
        "batch_size": 16,
        "learning_rate": 0.001,
    }
    assert len(job["tuning_plan_sha256"]) == 64
    assert job["provider_calls_applied"] == 0
    _assert_owner_trace(job, "KA-086")


def test_ka_082_owning_path_consumes_measured_predictions_and_labels(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    result = service.evaluate_model(
        model_id="measured-model",
        test_set="held-out-v1",
        predictions=[1, 0, 1, 1],
        labels=[1, 0, 0, 1],
        acceptance_accuracy=0.8,
        request_id="batch-10-evaluation",
        principal_id="owner-1",
    )

    assert result["status"] == "MEASURED"
    assert result["effects_applied"] == 0
    assert result["evaluation"]["metrics"] == {
        "accuracy": 0.75,
        "macro_precision": 0.8333,
        "macro_recall": 0.75,
        "macro_f1": 0.7333,
    }
    assert result["evaluation"]["meets_acceptance_threshold"] is False
    assert result["evaluation"]["predictions_generated"] is False
    states = result["lifecycle"]["trace_states"]["KA-082"]
    assert states == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]


def test_training_admission_rejects_path_escape_without_effect(tmp_path):
    dataset_root, artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes(artifact.read_bytes())

    with pytest.raises(
        ProviderModelLifecycleError,
        match="app-owned file name",
    ):
        _submit(service, artifact_name="../outside.jsonl")

    assert not (tmp_path / "admissions").exists()


def test_training_admission_rejects_mismatched_dataset_schema(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    with pytest.raises(
        ProviderModelLifecycleError,
        match="does not match",
    ):
        _submit(service, export_type="prm")

    assert not (tmp_path / "admissions").exists()


def test_training_admission_rejects_oversized_artifact_before_read(tmp_path):
    dataset_root, artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    with patch("pathlib.Path.is_file", return_value=True), patch(
        "pathlib.Path.stat"
    ) as mocked_stat:
        mocked_stat.return_value.st_size = 256 * 1024 * 1024 + 1
        with pytest.raises(
            ProviderModelLifecycleError,
            match="size is invalid",
        ):
            _submit(service)

    assert artifact.exists()
    assert not (tmp_path / "admissions").exists()


def test_model_evaluation_rejects_missing_measurements_as_owner_error(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )

    with pytest.raises(
        ProviderModelLifecycleError,
        match="evidence was rejected",
    ):
        service.evaluate_model(
            model_id="measured-model",
            test_set="held-out-v1",
            predictions=[],
            labels=[],
            acceptance_accuracy=0.8,
            request_id="batch-10-empty-evaluation",
            principal_id="owner-1",
        )

    assert not (tmp_path / "admissions").exists()


def test_training_admission_rejects_idempotency_reuse_without_overwrite(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    admission_root = tmp_path / "admissions"
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=admission_root,
    )
    original = _submit(service)
    target = admission_root / f"{original['job_id']}.json"
    original_bytes = target.read_bytes()

    with pytest.raises(
        ProviderModelLifecycleError,
        match="different request",
    ):
        _submit(service, model_name="different-model")

    assert target.read_bytes() == original_bytes


def test_training_admission_rejects_tampered_existing_receipt(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)
    admission_root = tmp_path / "admissions"
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=admission_root,
    )
    original = _submit(service)
    target = admission_root / f"{original['job_id']}.json"
    tampered = json.loads(target.read_text(encoding="utf-8"))
    tampered["training_started"] = True
    target.write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(
        ProviderModelLifecycleError,
        match="failed integrity validation",
    ):
        _submit(service)


def test_training_admission_rejects_tampered_ka_claim_before_effect(tmp_path):
    dataset_root, _artifact = _dataset(tmp_path)

    class TamperedCoordinator(ExtendedSubsystemCoordinator):
        def execute_operation_sync(self, **kwargs):
            execution = super().execute_operation_sync(**kwargs)
            if "KA-081" in execution.results:
                execution.results["KA-081"]["output"][
                    "training_started"
                ] = True
            return execution

    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
        coordinator=TamperedCoordinator(),
    )

    with pytest.raises(
        ProviderModelLifecycleError,
        match="unsupported effect claim",
    ):
        _submit(service)

    assert not (tmp_path / "admissions").exists()
