"""KA-089: bounded model-pruning proposals without artifact mutation."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Literal

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class KA089PruningInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "artifact_name": "qualified.onnx",
                    "artifact_sha256": "a" * 64,
                    "parameter_count": 1_000,
                    "target_sparsity": 0.2,
                }
            ]
        },
    )

    artifact_name: str = Field(min_length=1, max_length=200)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parameter_count: int = Field(ge=1, le=10_000_000_000_000)
    target_sparsity: float = Field(gt=0.0, le=0.95)
    method: Literal["magnitude_unstructured", "structured_channel"] = (
        "magnitude_unstructured"
    )
    importance_profile_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @field_validator("artifact_name")
    @classmethod
    def _file_name_only(cls, value: str) -> str:
        if Path(value).name != value:
            raise ValueError("artifact_name must be a file name")
        return value

    @field_validator("target_sparsity")
    @classmethod
    def _finite_sparsity(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("target_sparsity must be finite")
        return value


class KA089ModelPruning(KnowledgeAlgorithm):
    """Propose a pruning target without changing weights or estimating quality."""

    input_schema = KA089PruningInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-089"

    def _run_logic(self, input_data: KA089PruningInput) -> dict[str, Any]:
        planned_removal = int(
            input_data.parameter_count * input_data.target_sparsity
        )
        request = {
            "artifact_name": input_data.artifact_name,
            "artifact_sha256": input_data.artifact_sha256,
            "parameter_count": input_data.parameter_count,
            "target_sparsity": input_data.target_sparsity,
            "method": input_data.method,
            "importance_profile_sha256": input_data.importance_profile_sha256,
            "planned_parameter_removal": planned_removal,
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Proposing Model Pruning",
            {
                "artifact_name": input_data.artifact_name,
                "planned_parameter_removal": planned_removal,
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-pruning-proposal.v1",
            "status": "PROPOSED",
            "plan_sha256": plan_sha256,
            "request": request,
            "planned_parameter_removal": planned_removal,
            "quality_measurement_required": True,
            "pruning_applied": False,
            "weights_changed": False,
            "artifact_created": False,
            "retraining_applied": False,
            "provider_calls_applied": 0,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA089ModelPruning(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-089 failed: %s", exc)
        return {"success": False, "error": str(exc)}
