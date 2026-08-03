"""KA-088: deterministic A/B assignment and measured analysis proposals."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from typing import Any

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

logger = logging.getLogger(__name__)


class KA088MetricObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(ge=1, le=100_000_000)
    success_count: int = Field(ge=0, le=100_000_000)

    @model_validator(mode="after")
    def _successes_fit_sample(self) -> "KA088MetricObservation":
        if self.success_count > self.sample_count:
            raise ValueError("success_count cannot exceed sample_count")
        return self


class KA088ABInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "experiment_id": "release-candidate",
                    "traffic_split_percent": {
                        "control": 90.0,
                        "candidate": 10.0,
                    },
                }
            ]
        },
    )

    experiment_id: str = Field(min_length=1, max_length=200)
    traffic_split_percent: dict[str, float] = Field(
        min_length=2,
        max_length=2,
    )
    subject_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    observations: dict[str, KA088MetricObservation] = Field(
        default_factory=dict,
        max_length=2,
    )
    min_sample_size: int = Field(default=1_000, ge=1, le=10_000_000)

    @field_validator("traffic_split_percent")
    @classmethod
    def _valid_split(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != {"control", "candidate"}:
            raise ValueError("A/B variants must be exactly control and candidate")
        for name, percentage in value.items():
            if not str(name).strip() or len(str(name)) > 100:
                raise ValueError("variant names must contain 1 through 100 characters")
            if not math.isfinite(percentage) or percentage <= 0.0:
                raise ValueError("variant percentages must be finite and positive")
        if not math.isclose(sum(value.values()), 100.0, abs_tol=1e-9):
            raise ValueError("variant percentages must total 100")
        return value

    @model_validator(mode="after")
    def _observed_variants_are_declared(self) -> "KA088ABInput":
        if not set(self.observations).issubset(self.traffic_split_percent):
            raise ValueError("observations must reference declared variants")
        return self


class KA088ABTesting(KnowledgeAlgorithm):
    """Plan stable assignment and analyze only caller-supplied outcomes."""

    input_schema = KA088ABInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-088"

    def _run_logic(self, input_data: KA088ABInput) -> dict[str, Any]:
        variants = {
            "control": input_data.traffic_split_percent["control"],
            "candidate": input_data.traffic_split_percent["candidate"],
        }
        assigned_variant = (
            self._assign_variant(
                input_data.experiment_id,
                input_data.subject_sha256,
                variants,
            )
            if input_data.subject_sha256 is not None
            else None
        )
        analysis = self._analyze(
            variants,
            input_data.observations,
            min_sample_size=input_data.min_sample_size,
        )
        plan_payload = {
            "experiment_id": input_data.experiment_id,
            "traffic_split_percent": variants,
            "min_sample_size": input_data.min_sample_size,
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                plan_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Planning Model Experiment",
            {
                "experiment_id": input_data.experiment_id,
                "measurement_status": analysis["status"],
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-experiment-proposal.v1",
            "status": "PROPOSED",
            "plan_sha256": plan_sha256,
            "experiment_id": input_data.experiment_id,
            "traffic_split_percent": variants,
            "assigned_variant": assigned_variant,
            "assignment_basis": (
                "caller_supplied_sha256" if assigned_variant else None
            ),
            "analysis": analysis,
            "experiment_active": False,
            "assignment_applied": False,
            "routing_applied": False,
            "provider_calls_applied": 0,
            "persistence_applied": False,
        }

    @staticmethod
    def _assign_variant(
        experiment_id: str,
        subject_sha256: str,
        split: dict[str, float],
    ) -> str:
        digest = hashlib.sha256(
            f"{experiment_id}:{subject_sha256}".encode("utf-8")
        ).hexdigest()
        bucket = int(digest[:16], 16) / (16**16) * 100.0
        cumulative = 0.0
        for name, percentage in split.items():
            cumulative += percentage
            if bucket < cumulative:
                return name
        return next(reversed(split))

    @staticmethod
    def _analyze(
        variants: dict[str, float],
        observations: dict[str, KA088MetricObservation],
        *,
        min_sample_size: int,
    ) -> dict[str, Any]:
        if set(observations) != set(variants):
            return {
                "status": "MEASUREMENT_REQUIRED",
                "sufficient_data": False,
                "measured_rates": {},
                "absolute_lift": None,
                "z_score": None,
                "statistically_significant": None,
            }
        names = list(variants)
        first = observations[names[0]]
        second = observations[names[1]]
        first_rate = first.success_count / first.sample_count
        second_rate = second.success_count / second.sample_count
        pooled = (
            first.success_count + second.success_count
        ) / (first.sample_count + second.sample_count)
        standard_error = math.sqrt(
            pooled
            * (1.0 - pooled)
            * (1.0 / first.sample_count + 1.0 / second.sample_count)
        )
        z_score = (
            0.0
            if standard_error == 0.0
            else (second_rate - first_rate) / standard_error
        )
        sufficient = (
            first.sample_count >= min_sample_size
            and second.sample_count >= min_sample_size
        )
        return {
            "status": "MEASURED",
            "sufficient_data": sufficient,
            "measured_rates": {
                names[0]: round(first_rate, 6),
                names[1]: round(second_rate, 6),
            },
            "absolute_lift": round(second_rate - first_rate, 6),
            "z_score": round(z_score, 6),
            "statistically_significant": sufficient and abs(z_score) >= 1.96,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA088ABTesting(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-088 failed: %s", exc)
        return {"success": False, "error": str(exc)}
