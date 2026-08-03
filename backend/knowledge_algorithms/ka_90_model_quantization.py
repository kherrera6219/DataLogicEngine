"""KA-090: bounded model-quantization proposals without artifact creation."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Literal

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class KA090QuantizationInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "artifact_name": "qualified.onnx",
                    "artifact_sha256": "a" * 64,
                    "original_size_bytes": 1_024,
                    "source_bit_depth": 32,
                    "target_bit_depth": 8,
                }
            ]
        },
    )

    artifact_name: str = Field(min_length=1, max_length=200)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_size_bytes: int = Field(ge=1, le=256 * 1024 * 1024)
    source_bit_depth: Literal[16, 32] = 32
    target_bit_depth: Literal[4, 8, 16] = 8
    target_format: Literal["onnx", "safetensors", "tflite"] = "onnx"
    calibration_profile_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @field_validator("artifact_name")
    @classmethod
    def _file_name_only(cls, value: str) -> str:
        if Path(value).name != value:
            raise ValueError("artifact_name must be a file name")
        return value

    @model_validator(mode="after")
    def _reduces_precision(self) -> "KA090QuantizationInput":
        if self.target_bit_depth >= self.source_bit_depth:
            raise ValueError("target_bit_depth must be below source_bit_depth")
        return self


class KA090ModelQuantization(KnowledgeAlgorithm):
    """Propose precision reduction and report only theoretical size bounds."""

    input_schema = KA090QuantizationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-090"

    def _run_logic(self, input_data: KA090QuantizationInput) -> dict[str, Any]:
        theoretical_size_bytes = (
            input_data.original_size_bytes
            * input_data.target_bit_depth
            // input_data.source_bit_depth
        )
        request = {
            "artifact_name": input_data.artifact_name,
            "artifact_sha256": input_data.artifact_sha256,
            "original_size_bytes": input_data.original_size_bytes,
            "source_bit_depth": input_data.source_bit_depth,
            "target_bit_depth": input_data.target_bit_depth,
            "target_format": input_data.target_format,
            "calibration_profile_sha256": (
                input_data.calibration_profile_sha256
            ),
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Proposing Model Quantization",
            {
                "artifact_name": input_data.artifact_name,
                "target_bit_depth": input_data.target_bit_depth,
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-quantization-proposal.v1",
            "status": "PROPOSED",
            "plan_sha256": plan_sha256,
            "request": request,
            "theoretical_size_upper_bound_bytes": theoretical_size_bytes,
            "actual_size_measurement_required": True,
            "quantization_applied": False,
            "weights_changed": False,
            "artifact_created": False,
            "calibration_applied": False,
            "provider_calls_applied": 0,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA090ModelQuantization(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-090 failed: %s", exc)
        return {"success": False, "error": str(exc)}
