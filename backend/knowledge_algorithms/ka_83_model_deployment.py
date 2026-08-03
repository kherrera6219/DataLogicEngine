"""KA-083: dependency-bound model deployment-admission proposals.

The algorithm does not deploy a model, alter traffic, or perform rollback. It
binds measured health to version, experiment, pruning, and quantization plans so
an authoritative provider owner can record a release-preparation admission.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Literal

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class KA083HealthObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(ge=1, le=100_000_000)
    failure_count: int = Field(ge=0, le=100_000_000)
    p95_latency_ms: float = Field(ge=0.0, le=3_600_000.0)
    maximum_failure_rate: float = Field(ge=0.0, le=1.0)
    maximum_p95_latency_ms: float = Field(gt=0.0, le=3_600_000.0)

    @model_validator(mode="after")
    def _valid_observation(self) -> "KA083HealthObservation":
        if self.failure_count > self.sample_count:
            raise ValueError("failure_count cannot exceed sample_count")
        for value in (
            self.p95_latency_ms,
            self.maximum_failure_rate,
            self.maximum_p95_latency_ms,
        ):
            if not math.isfinite(value):
                raise ValueError("health measurements must be finite")
        return self


class KA083DeploymentInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "artifact_name": "qualified.onnx",
                    "artifact_sha256": "a" * 64,
                    "target_environment": "staging",
                    "health_observation": {
                        "sample_count": 100,
                        "failure_count": 0,
                        "p95_latency_ms": 100.0,
                        "maximum_failure_rate": 0.01,
                        "maximum_p95_latency_ms": 500.0,
                    },
                    "dependency_results": {
                        "KA-087": {
                            "schema_version": "dle.model-version-proposal.v1",
                            "status": "PROPOSED",
                            "plan_sha256": "b" * 64,
                            "proposed_version": "v1.0.1",
                            "request": {
                                "artifact_name": "qualified.onnx",
                                "artifact_sha256": "a" * 64,
                            },
                            "version_assigned": False,
                            "registry_write_applied": False,
                        },
                        "KA-088": {
                            "schema_version": "dle.model-experiment-proposal.v1",
                            "status": "PROPOSED",
                            "plan_sha256": "c" * 64,
                            "experiment_active": False,
                            "routing_applied": False,
                        },
                        "KA-089": {
                            "schema_version": "dle.model-pruning-proposal.v1",
                            "status": "PROPOSED",
                            "plan_sha256": "d" * 64,
                            "request": {
                                "artifact_name": "qualified.onnx",
                                "artifact_sha256": "a" * 64,
                            },
                            "pruning_applied": False,
                            "artifact_created": False,
                        },
                        "KA-090": {
                            "schema_version": "dle.model-quantization-proposal.v1",
                            "status": "PROPOSED",
                            "plan_sha256": "e" * 64,
                            "request": {
                                "artifact_name": "qualified.onnx",
                                "artifact_sha256": "a" * 64,
                            },
                            "quantization_applied": False,
                            "artifact_created": False,
                        },
                    },
                }
            ]
        },
    )

    artifact_name: str = Field(min_length=1, max_length=200)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_environment: Literal["staging", "production"]
    health_observation: KA083HealthObservation
    dependency_results: dict[str, dict[str, Any]]

    @field_validator("artifact_name")
    @classmethod
    def _file_name_only(cls, value: str) -> str:
        if Path(value).name != value:
            raise ValueError("artifact_name must be a file name")
        return value


class KA083ModelDeployment(KnowledgeAlgorithm):
    """Propose release admission after exact dependency and health checks."""

    input_schema = KA083DeploymentInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-083"

    def _run_logic(self, input_data: KA083DeploymentInput) -> dict[str, Any]:
        expected = {"KA-087", "KA-088", "KA-089", "KA-090"}
        if set(input_data.dependency_results) != expected:
            raise ValueError(
                "KA-083 requires exact KA-087 through KA-090 results"
            )
        dependency_plans: dict[str, str] = {}
        schemas = {
            "KA-087": "dle.model-version-proposal.v1",
            "KA-088": "dle.model-experiment-proposal.v1",
            "KA-089": "dle.model-pruning-proposal.v1",
            "KA-090": "dle.model-quantization-proposal.v1",
        }
        for canonical_id, schema in schemas.items():
            output = input_data.dependency_results[canonical_id]
            if output.get("schema_version") != schema:
                raise ValueError(
                    f"{canonical_id} returned an incompatible schema"
                )
            if output.get("status") != "PROPOSED":
                raise ValueError(f"{canonical_id} did not return a proposal")
            plan_sha256 = str(output.get("plan_sha256") or "")
            if len(plan_sha256) != 64 or any(
                character not in "0123456789abcdef"
                for character in plan_sha256
            ):
                raise ValueError(
                    f"{canonical_id} did not return a valid plan digest"
                )
            dependency_plans[canonical_id] = plan_sha256

        for canonical_id in ("KA-087", "KA-089", "KA-090"):
            output = input_data.dependency_results[canonical_id]
            request = output.get("request") or {}
            if (
                request.get("artifact_name") != input_data.artifact_name
                or request.get("artifact_sha256")
                != input_data.artifact_sha256
            ):
                raise ValueError(
                    f"{canonical_id} artifact identity does not match KA-083"
                )
        prohibited_claims = {
            "KA-087": ("version_assigned", "registry_write_applied"),
            "KA-088": ("experiment_active", "routing_applied"),
            "KA-089": ("pruning_applied", "artifact_created"),
            "KA-090": ("quantization_applied", "artifact_created"),
        }
        for canonical_id, fields in prohibited_claims.items():
            output = input_data.dependency_results[canonical_id]
            if any(output.get(field) is not False for field in fields):
                raise ValueError(
                    f"{canonical_id} returned an unsupported effect claim"
                )

        health = input_data.health_observation
        failure_rate = health.failure_count / health.sample_count
        healthy = (
            failure_rate <= health.maximum_failure_rate
            and health.p95_latency_ms <= health.maximum_p95_latency_ms
        )
        request = {
            "artifact_name": input_data.artifact_name,
            "artifact_sha256": input_data.artifact_sha256,
            "target_environment": input_data.target_environment,
            "proposed_version": input_data.dependency_results["KA-087"].get(
                "proposed_version"
            ),
            "dependency_plan_sha256": dict(sorted(dependency_plans.items())),
            "health": {
                "sample_count": health.sample_count,
                "failure_count": health.failure_count,
                "failure_rate": round(failure_rate, 8),
                "maximum_failure_rate": health.maximum_failure_rate,
                "p95_latency_ms": health.p95_latency_ms,
                "maximum_p95_latency_ms": health.maximum_p95_latency_ms,
                "healthy": healthy,
            },
        }
        proposal_id = "deployment-proposal-" + hashlib.sha256(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Proposing Model Deployment Admission",
            {
                "artifact_name": input_data.artifact_name,
                "target_environment": input_data.target_environment,
                "healthy": healthy,
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-deployment-proposal.v1",
            "proposal_id": proposal_id,
            "status": "PROPOSED" if healthy else "BLOCKED",
            "admission_recommended": healthy,
            "request": request,
            "requires_authoritative_service": True,
            "deployment_applied": False,
            "traffic_routing_applied": False,
            "rollback_applied": False,
            "provider_calls_applied": 0,
            "artifact_created": False,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA083ModelDeployment(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-083 failed: %s", exc)
        return {"success": False, "error": str(exc)}
