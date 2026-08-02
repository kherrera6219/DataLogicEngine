"""KA-086: measured hyperparameter candidate ranking and proposal creation."""

from __future__ import annotations

import hashlib
import itertools
import json
import logging
import math
from typing import Any

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class KA086Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    params: dict[str, Any]
    score: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=1)

    @field_validator("score")
    @classmethod
    def _finite_score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("observed scores must be finite")
        return value


class KA086TuningInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "model_type": "qualified-model",
                    "parameter_space": {"batch_size": [8]},
                    "observations": [],
                }
            ]
        },
    )

    model_type: str = Field(min_length=1, max_length=200)
    metric_name: str = Field(default="macro_f1", min_length=1, max_length=100)
    max_trials: int = Field(default=20, ge=1, le=1_000)
    parameter_space: dict[str, list[Any]] = Field(min_length=1, max_length=50)
    observations: list[KA086Observation] = Field(
        default_factory=list,
        max_length=1_000,
    )

    @field_validator("parameter_space")
    @classmethod
    def _validate_parameter_space(
        cls,
        value: dict[str, list[Any]],
    ) -> dict[str, list[Any]]:
        combinations = 1
        for name, candidates in value.items():
            if not str(name).strip() or len(str(name)) > 200:
                raise ValueError("parameter names must contain 1 through 200 characters")
            if not isinstance(candidates, list) or not candidates:
                raise ValueError("each parameter must declare at least one candidate")
            combinations *= len(candidates)
            if combinations > 100_000:
                raise ValueError("parameter space exceeds 100000 combinations")
            for candidate in candidates:
                if isinstance(candidate, (dict, list, set, tuple)):
                    raise ValueError("parameter candidates must be scalar")
                try:
                    json.dumps(candidate, allow_nan=False)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "parameter candidates must be finite JSON scalar values"
                    ) from exc
        return value


class KA086HyperparameterTuning(KnowledgeAlgorithm):
    """Rank exact measured candidates and expose unmeasured work as a proposal."""

    input_schema = KA086TuningInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-086"

    def _run_logic(self, input_data: KA086TuningInput) -> dict[str, Any]:
        candidates = self._candidate_grid(input_data.parameter_space)[
            : input_data.max_trials
        ]
        candidate_keys = {
            self._params_key(params): params for params in candidates
        }
        observations: dict[str, KA086Observation] = {}
        ignored_observations = 0
        for observation in input_data.observations:
            key = self._params_key(observation.params)
            if key not in candidate_keys:
                ignored_observations += 1
                continue
            current = observations.get(key)
            if current is None or observation.sample_count > current.sample_count:
                observations[key] = observation

        measured_trials = [
            {
                "params": candidate_keys[key],
                "score": round(observation.score, 6),
                "sample_count": observation.sample_count,
            }
            for key, observation in observations.items()
        ]
        measured_trials.sort(
            key=lambda row: (
                -float(row["score"]),
                self._params_key(row["params"]),
            )
        )
        unmeasured_candidates = [
            params
            for key, params in candidate_keys.items()
            if key not in observations
        ]
        best = measured_trials[0] if measured_trials else None
        proposal_payload = {
            "model_type": input_data.model_type,
            "metric_name": input_data.metric_name,
            "candidate_params": candidates,
            "unmeasured_candidates": unmeasured_candidates,
            "best_measured": best,
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                proposal_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Ranking Measured Hyperparameter Candidates",
            {
                "model_type": input_data.model_type,
                "candidate_count": len(candidates),
                "measured_count": len(measured_trials),
            },
        )
        return {
            "success": True,
            "schema_version": "dle.hyperparameter-tuning-proposal.v1",
            "status": "MEASURED" if best is not None else "MEASUREMENT_REQUIRED",
            "plan_sha256": plan_sha256,
            "metric": input_data.metric_name,
            "candidate_count": len(candidates),
            "measured_trial_count": len(measured_trials),
            "unmeasured_trial_count": len(unmeasured_candidates),
            "measured_trials": measured_trials,
            "unmeasured_candidates": unmeasured_candidates,
            "best_params": best["params"] if best is not None else None,
            "best_score": best["score"] if best is not None else None,
            "ignored_observation_count": ignored_observations,
            "strategy": "deterministic_grid_with_measured_ranking",
            "tuning_applied": False,
            "provider_calls_applied": 0,
        }

    @staticmethod
    def _candidate_grid(space: dict[str, list[Any]]) -> list[dict[str, Any]]:
        keys = sorted(space)
        return [
            dict(zip(keys, combination, strict=True))
            for combination in itertools.product(*(space[key] for key in keys))
        ]

    @staticmethod
    def _params_key(params: dict[str, Any]) -> str:
        return json.dumps(
            params,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA086HyperparameterTuning(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-086 failed: %s", exc)
        return {"success": False, "error": str(exc)}
