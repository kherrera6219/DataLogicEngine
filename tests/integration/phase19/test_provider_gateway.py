"""CP19-K provider/gateway owning-path qualification."""

from __future__ import annotations

import json

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleError,
)
from backend.llm_gateway.model_lifecycle import ProviderModelLifecycleService


def _assert_complete_trace(execution, canonical_id: str) -> None:
    events = execution.report.traces[canonical_id].events
    assert [event.state.value for event in events] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    executed = next(event for event in events if event.state.value == "executed")
    assert executed.result_trace_id


@pytest.mark.asyncio
async def test_ka_1072_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    execution = await coordinator.plan_provider_request(
        request_id="provider-ka-1072",
        trace_id="provider-trace-ka-1072",
        principal_id="owner-1",
        messages=[
            {"role": "system", "content": "Follow governed policy."},
            {"role": "user", "content": "Summarize the evidence."},
        ],
        token_budget=1_000,
    )
    output = coordinator.execution_outputs(execution)["KA-1072"]
    receipt = coordinator.bind_effect_receipt(
        service="ProviderGatewayService",
        operation="answer:provider_call",
        resource_id="provider-trace-ka-1072:1",
        request_payload={"message_sha256": "a" * 64},
        result_payload={"answer_sha256": "b" * 64},
        idempotency_key="provider-ka-1072:answer:1",
        ka_execution=execution,
    )

    assert output["status"] == "context_selected"
    assert output["selected_element_ids"] == ["message-0", "message-1"]
    assert receipt.ka_plan_id == execution.plan.plan_id
    assert receipt.ka_proposal_ids == []
    _assert_complete_trace(execution, "KA-1072")

    with pytest.raises(KnowledgeLifecycleError):
        await coordinator.plan_provider_request(
            request_id="provider-ka-1072-blocked",
            trace_id="provider-trace-ka-1072-blocked",
            principal_id="owner-1",
            messages=[
                {"role": "system", "content": "Required system policy."},
                {"role": "user", "content": "Required user request."},
            ],
            token_budget=1,
        )


@pytest.mark.asyncio
async def test_ka_084_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    execution = await coordinator.monitor_provider_result(
        request_id="provider-ka-084",
        trace_id="provider-trace-ka-084",
        principal_id="owner-1",
        duration_ms=350,
    )
    decision = coordinator.provider_monitoring_decision(execution)

    assert decision["status"] == "measured"
    assert decision["drift_detected"] is True
    assert decision["anomalies"] == ["LATENCY_SPIKE"]
    assert decision["alert_recommended"] is True
    assert decision["notification_applied"] is False
    _assert_complete_trace(execution, "KA-084")


def _training_admission(tmp_path):
    dataset_root = tmp_path / "datasets"
    dataset_root.mkdir()
    (dataset_root / "sft-qualified.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "question"},
                            {"role": "assistant", "content": "answer"},
                        ]
                    }
                ),
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "second"},
                            {"role": "assistant", "content": "response"},
                        ]
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )
    return service, service.submit_training_admission(
        artifact_name="sft-qualified.jsonl",
        export_type="sft",
        model_name="qualified-model",
        epochs=2,
        hyperparameters={},
        parameter_space={"batch_size": [8, 16]},
        tuning_observations=[
            {
                "params": {"batch_size": 16},
                "score": 0.91,
                "sample_count": 200,
            }
        ],
        idempotency_key="provider-training-admission",
        request_id="provider-training-request",
        principal_id="owner-1",
    )


def _assert_model_trace(job: dict, canonical_id: str) -> None:
    states = job["lifecycle"]["trace_states"][canonical_id]
    assert states[:2] == ["planned", "candidate"]
    assert "selected" in states
    assert "executed" in states
    if canonical_id in {
        "KA-085",
        "KA-086",
        "KA-087",
        "KA-088",
        "KA-089",
        "KA-090",
    }:
        assert "dependency" in states
    if canonical_id in {"KA-081", "KA-083"}:
        assert states[-1] == "effect_proposed"


def test_ka_081_owning_path(tmp_path):
    service, job = _training_admission(tmp_path)
    repeated = service.submit_training_admission(
        artifact_name="sft-qualified.jsonl",
        export_type="sft",
        model_name="qualified-model",
        epochs=2,
        hyperparameters={},
        parameter_space={"batch_size": [8, 16]},
        tuning_observations=[
            {
                "params": {"batch_size": 16},
                "score": 0.91,
                "sample_count": 200,
            }
        ],
        idempotency_key="provider-training-admission",
        request_id="provider-training-request",
        principal_id="owner-1",
    )

    assert job == repeated
    assert job["status"] == "ADMISSION_RECORDED"
    assert job["training_execution_available"] is False
    assert job["training_started"] is False
    assert job["model_artifact_created"] is False
    assert job["authoritative_effect_receipt"]["operation"] == (
        "record_model_training_admission"
    )
    _assert_model_trace(job, "KA-081")


def test_ka_082_owning_path(tmp_path):
    dataset_root = tmp_path / "datasets"
    service = ProviderModelLifecycleService(
        dataset_root=dataset_root,
        admission_root=tmp_path / "admissions",
    )
    result = service.evaluate_model(
        model_id="qualified-model",
        test_set="held-out-v1",
        predictions=[1, 0, 1, 1],
        labels=[1, 0, 0, 1],
        acceptance_accuracy=0.8,
        request_id="provider-evaluation-request",
        principal_id="owner-1",
    )

    assert result["status"] == "MEASURED"
    assert result["effects_applied"] == 0
    assert result["evaluation"]["metrics"]["accuracy"] == 0.75
    assert result["evaluation"]["predictions_generated"] is False
    assert result["lifecycle"]["trace_states"]["KA-082"][-1] == "executed"


def test_ka_085_owning_path(tmp_path):
    _service, job = _training_admission(tmp_path)

    assert job["dataset"]["feature_profile_records"] == 2
    assert len(job["feature_plan_sha256"]) == 64
    assert "question" not in json.dumps(job)
    assert "answer" not in json.dumps(job)
    _assert_model_trace(job, "KA-085")


def test_ka_086_owning_path(tmp_path):
    _service, job = _training_admission(tmp_path)

    assert job["hyperparameters"] == {"batch_size": 16}
    assert len(job["tuning_plan_sha256"]) == 64
    assert job["provider_calls_applied"] == 0
    _assert_model_trace(job, "KA-086")


def _release_preparation(tmp_path):
    model_root = tmp_path / "models"
    model_root.mkdir(exist_ok=True)
    (model_root / "qualified.onnx").write_bytes(b"bounded-model-artifact")
    service = ProviderModelLifecycleService(
        dataset_root=tmp_path / "datasets",
        admission_root=tmp_path / "training-admissions",
        model_root=model_root,
        release_root=tmp_path / "release-preparations",
    )
    record = service.submit_release_preparation(
        artifact_name="qualified.onnx",
        current_version="v1.2.3",
        increment="patch",
        source_commit="a" * 40,
        release_channel="candidate",
        target_environment="staging",
        parameter_count=1_000_000,
        target_sparsity=0.2,
        pruning_method="magnitude_unstructured",
        importance_profile_sha256="b" * 64,
        source_bit_depth=32,
        target_bit_depth=8,
        target_format="onnx",
        calibration_profile_sha256="c" * 64,
        experiment_id="release-candidate-v1-2-4",
        traffic_split_percent={"control": 90, "candidate": 10},
        experiment_observations={},
        min_sample_size=1_000,
        health_observation={
            "sample_count": 10_000,
            "failure_count": 5,
            "p95_latency_ms": 180.0,
            "maximum_failure_rate": 0.01,
            "maximum_p95_latency_ms": 500.0,
        },
        idempotency_key="provider-release-preparation",
        request_id="provider-release-request",
        principal_id="owner-1",
    )
    return service, record


def test_ka_083_owning_path(tmp_path):
    _service, record = _release_preparation(tmp_path)

    assert record["status"] == "RELEASE_PREPARATION_RECORDED"
    assert record["deployment_started"] is False
    assert record["traffic_routing_applied"] is False
    assert record["provider_calls_applied"] == 0
    assert record["authoritative_effect_receipt"]["operation"] == (
        "record_model_release_preparation"
    )
    _assert_model_trace(record, "KA-083")


def test_ka_087_owning_path(tmp_path):
    _service, record = _release_preparation(tmp_path)

    assert record["proposed_version"] == "v1.2.4"
    assert record["version_proposal"]["registry_write_applied"] is False
    _assert_model_trace(record, "KA-087")


def test_ka_088_owning_path(tmp_path):
    _service, record = _release_preparation(tmp_path)

    assert record["experiment_proposal"]["analysis_status"] == (
        "MEASUREMENT_REQUIRED"
    )
    assert record["experiment_proposal"]["routing_applied"] is False
    _assert_model_trace(record, "KA-088")


def test_ka_089_owning_path(tmp_path):
    _service, record = _release_preparation(tmp_path)

    assert record["pruning_proposal"]["planned_parameter_removal"] == 200_000
    assert record["pruning_proposal"]["pruning_applied"] is False
    _assert_model_trace(record, "KA-089")


def test_ka_090_owning_path(tmp_path):
    _service, record = _release_preparation(tmp_path)

    assert record["quantization_proposal"][
        "actual_size_measurement_required"
    ] is True
    assert record["quantization_proposal"]["quantization_applied"] is False
    _assert_model_trace(record, "KA-090")
