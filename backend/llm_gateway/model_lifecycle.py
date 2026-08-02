"""Provider-owned model preparation and measured evaluation boundary.

The service deliberately stops at a durable training-admission record.  The
application has no bundled training worker, so neither this module nor KA-081
claims that epochs, checkpoints, provider calls, or model artifacts exist.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleError
from backend.knowledge_algorithms.selection import KATraceState

MAX_PREPARATION_ARTIFACT_BYTES = 256 * 1024 * 1024


class ProviderModelLifecycleError(ExtendedSubsystemError):
    """Raised when model preparation cannot be admitted truthfully."""


@dataclass(frozen=True, slots=True)
class DatasetArtifactProfile:
    """Content-free measurements of one app-owned dataset artifact."""

    artifact_name: str
    path: Path
    export_type: str
    format: str
    sha256: str
    size_bytes: int
    row_count: int
    feature_records: list[dict[str, Any]]

    def evidence(self) -> dict[str, Any]:
        return {
            "artifact_name": self.artifact_name,
            "export_type": self.export_type,
            "format": self.format,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "row_count": self.row_count,
            "feature_profile_records": len(self.feature_records),
        }


class ProviderModelLifecycleService:
    """Own model-preparation effects and consume measured KA decisions."""

    def __init__(
        self,
        *,
        dataset_root: str | os.PathLike[str],
        admission_root: str | os.PathLike[str],
        coordinator: ExtendedSubsystemCoordinator | None = None,
    ) -> None:
        self.dataset_root = Path(dataset_root).resolve()
        self.admission_root = Path(admission_root).resolve()
        self.coordinator = coordinator or ExtendedSubsystemCoordinator()

    def submit_training_admission(
        self,
        *,
        artifact_name: str,
        export_type: str,
        model_name: str,
        epochs: int,
        hyperparameters: dict[str, Any],
        parameter_space: dict[str, list[Any]],
        tuning_observations: list[dict[str, Any]],
        idempotency_key: str,
        request_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        """Persist one idempotent admission after the canonical KA chain passes."""
        self._validate_identity(
            idempotency_key=idempotency_key,
            request_id=request_id,
            principal_id=principal_id,
        )
        artifact = self._profile_artifact(
            artifact_name=artifact_name,
            export_type=export_type,
        )
        ka_inputs = {
            "KA-085": {"raw_data": artifact.feature_records},
            "KA-086": {
                "model_type": model_name,
                "parameter_space": parameter_space,
                "observations": tuning_observations,
            },
        }
        provisional = self._execute_required(
            owner="provider_gateway",
            operation="model_lifecycle",
            requested_ids=["KA-085", "KA-086"],
            ka_inputs=ka_inputs,
            request_id=f"{request_id}:preparation",
            run_id=f"model-preparation:{request_id}",
            max_effects=0,
            session_id=request_id,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="model_preparation",
            required=True,
        )
        provisional_outputs = self.coordinator.execution_outputs(provisional)
        tuning_output = provisional_outputs.get("KA-086") or {}
        selected_hyperparameters = tuning_output.get("best_params")
        if selected_hyperparameters is None:
            selected_hyperparameters = dict(hyperparameters)
        elif hyperparameters and hyperparameters != selected_hyperparameters:
            raise ProviderModelLifecycleError(
                "Requested hyperparameters conflict with the best measured candidate"
            )

        execution = self._execute_required(
            owner="provider_gateway",
            operation="model_lifecycle",
            requested_ids=["KA-081"],
            ka_inputs={
                **ka_inputs,
                "KA-081": {
                    "dataset_id": artifact.artifact_name,
                    "dataset_sha256": artifact.sha256,
                    "dataset_format": artifact.export_type,
                    "model_name": model_name,
                    "training_samples": artifact.row_count,
                    "feature_profile_records": len(artifact.feature_records),
                    "epochs": epochs,
                    "hyperparameters": selected_hyperparameters,
                },
            },
            request_id=request_id,
            run_id=f"model-admission:{request_id}",
            max_effects=1,
            session_id=request_id,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="model_preparation",
            service_capabilities={"provider_gateway_service"},
            required=True,
        )
        outputs = self._validate_training_execution(
            execution,
            artifact=artifact,
        )
        proposal = outputs["KA-081"]
        request_payload = {
            "artifact": artifact.evidence(),
            "model_name": model_name,
            "epochs": epochs,
            "hyperparameters": selected_hyperparameters,
            "parameter_space": parameter_space,
            "tuning_observations": tuning_observations,
            "principal_sha256": self._sha256_text(principal_id),
        }
        request_sha256 = self.coordinator.sha256_payload(request_payload)
        job_id = "model-admission-" + self._sha256_text(idempotency_key)[:24]
        target = self.admission_root / f"{job_id}.json"
        existing = self._read_existing(target, request_sha256=request_sha256)
        if existing is not None:
            return existing

        job = {
            "schema_version": "dle.provider-model-training-admission.v1",
            "job_id": job_id,
            "status": "ADMISSION_RECORDED",
            "request_sha256": request_sha256,
            "dataset": artifact.evidence(),
            "model_name": model_name,
            "epochs_requested": int(epochs),
            "hyperparameters": selected_hyperparameters,
            "feature_plan_sha256": proposal["request"][
                "feature_plan_sha256"
            ],
            "tuning_plan_sha256": proposal["request"][
                "tuning_plan_sha256"
            ],
            "training_proposal_id": proposal["proposal_id"],
            "training_execution_available": False,
            "training_started": False,
            "worker_assigned": False,
            "epochs_run": 0,
            "checkpoints_created": 0,
            "model_artifact_created": False,
            "provider_calls_applied": 0,
            "lifecycle": self._lifecycle_evidence(execution),
            "preparation_lifecycle": self._lifecycle_evidence(provisional),
        }
        receipt = self.coordinator.bind_effect_receipt(
            service=self.__class__.__name__,
            operation="record_model_training_admission",
            resource_id=job_id,
            request_payload=request_payload,
            result_payload=job,
            idempotency_key=idempotency_key,
            ka_execution=execution,
            proposal_ids=[proposal["proposal_id"]],
        ).to_dict()
        job["authoritative_effect_receipt"] = receipt
        return self._write_once(target, job)

    def evaluate_model(
        self,
        *,
        model_id: str,
        test_set: str,
        predictions: list[Any],
        labels: list[Any],
        acceptance_accuracy: float,
        request_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        """Consume a measured evaluation without creating an artifact or effect."""
        self._validate_identity(
            idempotency_key="evaluation-only",
            request_id=request_id,
            principal_id=principal_id,
        )
        execution = self._execute_required(
            owner="provider_gateway",
            operation="model_lifecycle",
            requested_ids=["KA-082"],
            ka_inputs={
                "KA-082": {
                    "model_id": model_id,
                    "test_set": test_set,
                    "predictions": predictions,
                    "labels": labels,
                    "acceptance_accuracy": acceptance_accuracy,
                }
            },
            request_id=request_id,
            run_id=f"model-evaluation:{request_id}",
            max_effects=0,
            session_id=request_id,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="model_evaluation",
            required=True,
        )
        outputs = self.coordinator.execution_outputs(execution)
        evaluation = outputs.get("KA-082") or {}
        if (
            evaluation.get("schema_version") != "dle.model-evaluation.v1"
            or evaluation.get("status") != "MEASURED"
            or evaluation.get("sample_count") != len(labels)
            or evaluation.get("predictions_generated") is not False
            or evaluation.get("evaluation_artifact_created") is not False
        ):
            raise ProviderModelLifecycleError(
                "KA-082 returned incomplete or unmeasured evaluation evidence"
            )
        return {
            "schema_version": "dle.provider-model-evaluation.v1",
            "status": "MEASURED",
            "evaluation": evaluation,
            "lifecycle": self._lifecycle_evidence(execution),
            "effects_applied": 0,
        }

    def _profile_artifact(
        self,
        *,
        artifact_name: str,
        export_type: str,
    ) -> DatasetArtifactProfile:
        artifact_name = str(artifact_name or "").strip()
        export_type = str(export_type or "").strip().lower()
        if not artifact_name or Path(artifact_name).name != artifact_name:
            raise ProviderModelLifecycleError(
                "Dataset artifact must be an app-owned file name"
            )
        if export_type not in {"sft", "dpo", "prm"}:
            raise ProviderModelLifecycleError("Unsupported dataset export type")
        path = (self.dataset_root / artifact_name).resolve()
        try:
            path.relative_to(self.dataset_root)
        except ValueError as exc:
            raise ProviderModelLifecycleError(
                "Dataset artifact escapes the app-owned dataset root"
            ) from exc
        if not path.is_file():
            raise ProviderModelLifecycleError("Dataset artifact does not exist")
        size_bytes = path.stat().st_size
        if size_bytes <= 0 or size_bytes > MAX_PREPARATION_ARTIFACT_BYTES:
            raise ProviderModelLifecycleError("Dataset artifact size is invalid")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)

        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            row_count, features = self._profile_jsonl(
                path,
                export_type=export_type,
            )
            format_name = "jsonl"
        elif suffix == ".parquet":
            row_count, features = self._profile_parquet(
                path,
                export_type=export_type,
            )
            format_name = "parquet"
        else:
            raise ProviderModelLifecycleError(
                "Dataset artifact must be JSONL or Parquet"
            )
        if row_count < 1 or not features:
            raise ProviderModelLifecycleError(
                "Dataset artifact contains no training records"
            )
        return DatasetArtifactProfile(
            artifact_name=artifact_name,
            path=path,
            export_type=export_type,
            format=format_name,
            sha256=digest.hexdigest(),
            size_bytes=size_bytes,
            row_count=row_count,
            feature_records=features,
        )

    @staticmethod
    def _profile_jsonl(
        path: Path,
        *,
        export_type: str,
    ) -> tuple[int, list[dict[str, Any]]]:
        features: list[dict[str, Any]] = []
        with path.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if line_number > 10_000:
                    raise ProviderModelLifecycleError(
                        "Dataset exceeds the 10000-row preparation limit"
                    )
                line = raw_line.rstrip(b"\r\n")
                if not line or len(line) > 4 * 1024 * 1024:
                    raise ProviderModelLifecycleError(
                        "Dataset contains an empty or oversized JSONL record"
                    )
                try:
                    row = json.loads(
                        line,
                        parse_constant=ProviderModelLifecycleService._reject_json_constant,
                    )
                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    ValueError,
                ) as exc:
                    raise ProviderModelLifecycleError(
                        "Dataset contains invalid JSONL"
                    ) from exc
                if not isinstance(row, dict):
                    raise ProviderModelLifecycleError(
                        "Dataset JSONL records must be objects"
                    )
                ProviderModelLifecycleService._validate_dataset_row(
                    row,
                    export_type=export_type,
                )
                messages = row.get("messages")
                completions = row.get("completions")
                features.append(
                    {
                        "serialized_bytes": len(line),
                        "top_level_fields": len(row),
                        "message_count": (
                            len(messages) if isinstance(messages, list) else 0
                        ),
                        "completion_count": (
                            len(completions)
                            if isinstance(completions, list)
                            else 0
                        ),
                        "dataset_format": path.suffix.lower(),
                    }
                )
        return len(features), features

    @staticmethod
    def _profile_parquet(
        path: Path,
        *,
        export_type: str,
    ) -> tuple[int, list[dict[str, Any]]]:
        try:
            import pyarrow.parquet as parquet
        except ImportError as exc:  # pragma: no cover - optional installation
            raise ProviderModelLifecycleError(
                "Parquet preparation requires PyArrow"
            ) from exc
        try:
            metadata = parquet.ParquetFile(path).metadata
        except Exception as exc:  # noqa: BLE001 - parser trust boundary
            raise ProviderModelLifecycleError(
                "Dataset contains invalid Parquet data"
            ) from exc
        row_count = int(metadata.num_rows)
        if row_count > 10_000:
            raise ProviderModelLifecycleError(
                "Dataset exceeds the 10000-row preparation limit"
            )
        schema_names = set(parquet.ParquetFile(path).schema_arrow.names)
        required_columns = {
            "sft": {"messages"},
            "dpo": {"prompt", "chosen", "rejected"},
            "prm": {"prompt", "completions", "labels"},
        }[export_type]
        if not required_columns.issubset(schema_names):
            raise ProviderModelLifecycleError(
                "Dataset schema does not match its declared export type"
            )
        features = [
            {
                "row_count": row_count,
                "row_group_count": int(metadata.num_row_groups),
                "column_count": int(metadata.num_columns),
                "serialized_bytes": int(path.stat().st_size),
                "dataset_format": path.suffix.lower(),
            }
        ]
        return row_count, features

    def _execute_required(self, **kwargs: Any) -> Any:
        try:
            return self.coordinator.execute_operation_sync(**kwargs)
        except ProviderModelLifecycleError:
            raise
        except KnowledgeLifecycleError as exc:
            raise ProviderModelLifecycleError(
                "Model lifecycle evidence was rejected"
            ) from exc

    @staticmethod
    def _validate_dataset_row(
        row: dict[str, Any],
        *,
        export_type: str,
    ) -> None:
        if export_type == "sft":
            valid = isinstance(row.get("messages"), list) and bool(
                row["messages"]
            )
        elif export_type == "dpo":
            valid = all(
                isinstance(row.get(name), list) and bool(row[name])
                for name in ("prompt", "chosen", "rejected")
            )
        else:
            completions = row.get("completions")
            labels = row.get("labels")
            valid = bool(
                isinstance(row.get("prompt"), str)
                and row["prompt"].strip()
                and isinstance(completions, list)
                and completions
                and isinstance(labels, list)
                and len(labels) == len(completions)
            )
        if not valid:
            raise ProviderModelLifecycleError(
                "Dataset schema does not match its declared export type"
            )

    @staticmethod
    def _reject_json_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    @staticmethod
    def _validate_training_execution(
        execution: Any,
        *,
        artifact: DatasetArtifactProfile,
    ) -> dict[str, dict[str, Any]]:
        expected = {"KA-081", "KA-085", "KA-086"}
        outputs = ExtendedSubsystemCoordinator.execution_outputs(execution)
        if set(outputs) != expected:
            raise ProviderModelLifecycleError(
                "Model preparation omitted required canonical decisions"
            )
        proposal = outputs["KA-081"]
        feature = outputs["KA-085"]
        tuning = outputs["KA-086"]
        if (
            proposal.get("status") != "PROPOSED"
            or proposal.get("training_started") is not False
            or proposal.get("model_artifact_created") is not False
            or proposal.get("request", {}).get("dataset_sha256")
            != artifact.sha256
            or feature.get("persistence_applied") is not False
            or tuning.get("tuning_applied") is not False
            or tuning.get("provider_calls_applied") != 0
        ):
            raise ProviderModelLifecycleError(
                "Model preparation returned an unsupported effect claim"
            )
        return outputs

    @staticmethod
    def _lifecycle_evidence(execution: Any) -> dict[str, Any]:
        evidence = ExtendedSubsystemCoordinator.lifecycle_evidence(execution)
        evidence["trace_states"] = {
            canonical_id: [event.state.value for event in trace.events]
            for canonical_id, trace in sorted(execution.report.traces.items())
        }
        for canonical_id in execution.executed_ids:
            states = execution.report.traces[canonical_id].events
            if not any(event.state is KATraceState.EXECUTED for event in states):
                raise ProviderModelLifecycleError(
                    f"{canonical_id} has no committed execution trace"
                )
        return evidence

    @staticmethod
    def _validate_identity(
        *,
        idempotency_key: str,
        request_id: str,
        principal_id: str,
    ) -> None:
        if not 8 <= len(str(idempotency_key or "")) <= 200:
            raise ProviderModelLifecycleError(
                "Idempotency key must contain 8 through 200 characters"
            )
        if not 1 <= len(str(request_id or "")) <= 200:
            raise ProviderModelLifecycleError(
                "Request ID must contain 1 through 200 characters"
            )
        if not 1 <= len(str(principal_id or "")) <= 200:
            raise ProviderModelLifecycleError(
                "Principal ID must contain 1 through 200 characters"
            )

    def _read_existing(
        self,
        target: Path,
        *,
        request_sha256: str,
    ) -> dict[str, Any] | None:
        if not target.exists():
            return None
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProviderModelLifecycleError(
                "Existing training admission record is unreadable"
            ) from exc
        if payload.get("request_sha256") != request_sha256:
            raise ProviderModelLifecycleError(
                "Idempotency key was already used for a different request"
            )
        self._validate_existing_receipt(target, payload)
        return payload

    def _validate_existing_receipt(
        self,
        target: Path,
        payload: dict[str, Any],
    ) -> None:
        receipt = payload.get("authoritative_effect_receipt")
        job_id = str(payload.get("job_id") or "")
        base_payload = dict(payload)
        base_payload.pop("authoritative_effect_receipt", None)
        valid = bool(
            payload.get("schema_version")
            == "dle.provider-model-training-admission.v1"
            and payload.get("status") == "ADMISSION_RECORDED"
            and job_id == target.stem
            and isinstance(receipt, dict)
            and receipt.get("schema_version")
            == "dle.authoritative-effect-receipt.v1"
            and receipt.get("status") == "applied"
            and receipt.get("service") == self.__class__.__name__
            and receipt.get("operation") == "record_model_training_admission"
            and receipt.get("resource_id") == job_id
            and receipt.get("request_sha256") == payload.get("request_sha256")
            and job_id
            == "model-admission-"
            + self._sha256_text(str(receipt.get("idempotency_key") or ""))[:24]
            and hmac.compare_digest(
                str(receipt.get("result_sha256") or ""),
                self.coordinator.sha256_payload(base_payload),
            )
        )
        if not valid:
            raise ProviderModelLifecycleError(
                "Existing training admission record failed integrity validation"
            )

    def _write_once(
        self,
        target: Path,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self.admission_root.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            return payload
        except FileExistsError:
            existing = self._read_existing(
                target,
                request_sha256=str(payload["request_sha256"]),
            )
            if existing is None:
                raise ProviderModelLifecycleError(
                    "Training admission write conflicted"
                )
            return existing

    @staticmethod
    def _sha256_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
