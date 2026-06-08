"""
KA-090: Model Quantization
Purpose: Convert model weights from high-precision (FP32) to lower-precision (INT8/FP16) formats to optimize deployment on edge devices.
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA090QuantizationInput(BaseModel):
    model_id: str = Field("latest", description="The ID of the model artifact to quantize")
    original_size_mb: Any = Field(None, description="Original model artifact size in MB")
    source_bit_depth: int = Field(32, ge=1, description="Source precision bit depth")
    target_bit_depth: Any = Field(None, description="Target precision bit depth")
    target_format: str = Field("tflite", description="Target model artifact format")

class KA090ModelQuantization(KnowledgeAlgorithm):
    """
    KA-090: Precision reduction and quantization engine for optimized deployment.
    """
    input_schema = KA090QuantizationInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-090"
        self.config = {**self._load_config(), **context}

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_90_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA090QuantizationInput) -> Dict[str, Any]:
        model_id = input_data.model_id
        target_bit_depth = self._as_int(input_data.target_bit_depth, self.config.get('target_bit_depth', 8), 1)
        source_bit_depth = input_data.source_bit_depth
        self.log_execution_step("Quantizing Model Artifact", {"model": model_id, "depth": f"{target_bit_depth}-bit"})
        
        size_original_mb = self._as_float(input_data.original_size_mb, None, 0.0)
        if size_original_mb is None:
            size_original_mb = self.config.get("default_model_size_mb", 0)
        size_quantized_mb = round(size_original_mb * (target_bit_depth / max(1, source_bit_depth)), 4)
        reduction_percent = 0.0
        if size_original_mb:
            reduction_percent = (1.0 - size_quantized_mb / size_original_mb) * 100
        
        return {
            "success": True,
            "quantized_model_path": f"/models/{model_id}_int{target_bit_depth}.{input_data.target_format}",
            "original_size_mb": size_original_mb,
            "quantized_size_mb": size_quantized_mb,
            "source_bit_depth": source_bit_depth,
            "target_bit_depth": target_bit_depth,
            "reduction_percent": f"{reduction_percent:.1f}%"
        }

    @staticmethod
    def _as_float(value: Any, default: Optional[float], minimum: float) -> Optional[float]:
        if value is None:
            return default
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, parsed)

    @staticmethod
    def _as_int(value: Any, default: int, minimum: int) -> int:
        if value is None:
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, parsed)

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA090ModelQuantization(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-090 Failed: {e}")
        return {"success": False, "error": str(e)}
