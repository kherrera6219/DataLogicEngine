"""KA-081: bounded model-training admission proposals.

The algorithm never starts a trainer, creates checkpoints, or reports training
metrics.  It validates and fingerprints a proposed job so the authoritative
provider model-lifecycle service can decide whether to persist the admission.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class KA081TrainingInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "dataset_id": "qualified.jsonl",
                    "dataset_sha256": "a" * 64,
                    "dataset_format": "sft",
                    "model_name": "qualified-model",
                    "training_samples": 1,
                    "feature_profile_records": 1,
                    "epochs": 1,
                    "hyperparameters": {},
                    "dependency_results": {
                        "KA-085": {
                            "schema_version": "dle.feature-engineering-result.v1",
                            "plan_sha256": "b" * 64,
                            "records_processed": 1,
                        },
                        "KA-086": {
                            "schema_version": "dle.hyperparameter-tuning-proposal.v1",
                            "plan_sha256": "c" * 64,
                            "status": "MEASUREMENT_REQUIRED",
                            "best_params": None,
                        },
                    },
                }
            ]
        },
    )

    dataset_id: str = Field(min_length=1, max_length=200)
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_format: Literal["sft", "dpo", "prm"]
    model_name: str = Field(min_length=1, max_length=200)
    training_samples: int = Field(ge=1, le=10_000_000)
    feature_profile_records: int = Field(ge=1, le=10_000)
    epochs: int = Field(ge=1, le=100)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    dependency_results: dict[str, dict[str, Any]]

    @field_validator("hyperparameters")
    @classmethod
    def _bounded_hyperparameters(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 50:
            raise ValueError("hyperparameters exceed the 50-field limit")
        try:
            encoded = json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "hyperparameters must contain finite JSON values"
            ) from exc
        if len(encoded.encode("utf-8")) > 32_768:
            raise ValueError("hyperparameters exceed the 32 KiB limit")
        return value


class KA081ModelTraining(KnowledgeAlgorithm):
    """Produce an unapplied, deterministic training-admission proposal."""

    input_schema = KA081TrainingInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-081"

    def _run_logic(self, input_data: KA081TrainingInput) -> dict[str, Any]:
        if set(input_data.dependency_results) != {"KA-085", "KA-086"}:
            raise ValueError("KA-081 requires exact KA-085 and KA-086 results")
        feature_result = input_data.dependency_results["KA-085"]
        tuning_result = input_data.dependency_results["KA-086"]
        feature_plan_sha256 = self._dependency_plan_sha256(
            feature_result,
            expected_schema="dle.feature-engineering-result.v1",
            dependency="KA-085",
        )
        tuning_plan_sha256 = self._dependency_plan_sha256(
            tuning_result,
            expected_schema="dle.hyperparameter-tuning-proposal.v1",
            dependency="KA-086",
        )
        if int(feature_result.get("records_processed") or 0) != (
            input_data.feature_profile_records
        ):
            raise ValueError(
                "KA-085 record count does not match the declared feature profile"
            )
        best_params = tuning_result.get("best_params")
        if best_params is not None and best_params != input_data.hyperparameters:
            raise ValueError(
                "training hyperparameters do not match the best measured KA-086 candidate"
            )
        request = {
            "dataset_id": input_data.dataset_id,
            "dataset_sha256": input_data.dataset_sha256,
            "dataset_format": input_data.dataset_format,
            "model_name": input_data.model_name,
            "training_samples": input_data.training_samples,
            "feature_profile_records": input_data.feature_profile_records,
            "epochs": input_data.epochs,
            "hyperparameters": input_data.hyperparameters,
            "feature_plan_sha256": feature_plan_sha256,
            "tuning_plan_sha256": tuning_plan_sha256,
            "tuning_measurement_status": tuning_result.get("status"),
        }
        proposal_id = "training-proposal-" + hashlib.sha256(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Proposing Model Training Admission",
            {
                "dataset_id": input_data.dataset_id,
                "model_name": input_data.model_name,
                "training_samples": input_data.training_samples,
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-training-proposal.v1",
            "proposal_id": proposal_id,
            "status": "PROPOSED",
            "request": request,
            "requires_authoritative_service": True,
            "training_started": False,
            "epochs_run": 0,
            "checkpoints_created": 0,
            "model_artifact_created": False,
            "provider_call_applied": False,
        }

    @staticmethod
    def _dependency_plan_sha256(
        output: dict[str, Any],
        *,
        expected_schema: str,
        dependency: str,
    ) -> str:
        if output.get("schema_version") != expected_schema:
            raise ValueError(f"{dependency} returned an incompatible schema")
        digest = str(output.get("plan_sha256") or "")
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"{dependency} did not return a valid plan digest")
        return digest


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA081ModelTraining(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-081 failed: %s", exc)
        return {"success": False, "error": str(exc)}
