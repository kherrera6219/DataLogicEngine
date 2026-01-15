from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Union
import logging
import time
from datetime import datetime, UTC
from pydantic import BaseModel, Field, ValidationError

# Configure structured logging
logger = logging.getLogger("ka_engine")

class KAInput(BaseModel):
    """Standard input schema for KAs. Can be subclassed by specific KAs."""
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KAResult(BaseModel):
    """Standard result schema for KAs."""
    ka_id: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    execution_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None

class KnowledgeAlgorithm(ABC):
    """
    Enterprise-grade base class for all Knowledge Algorithms (KAs).
    
    Includes Pydantic validation, performance telemetry, and standardized logging.
    """
    
    # KAs should override these to enforce strict input/output validation
    input_schema: Type[BaseModel] = KAInput
    
    def __init__(self, config: Dict[str, Any], graph_manager: Any = None, 
                 memory_manager: Any = None, united_system_manager: Any = None):
        """
        Initialize the Knowledge Algorithm with system dependencies.
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.ka_id = self.__class__.__name__ # Default, usually overridden
        self.logger = logging.getLogger(f"ka.{self.ka_id}")

    @abstractmethod
    def _run_logic(self, input_data: BaseModel) -> Dict[str, Any]:
        """
        Core implementation logic for the KA. 
        Must be implemented by subclasses.
        """
        pass

    def run(self, input_data: Union[Dict[str, Any], BaseModel]) -> Dict[str, Any]:
        """
        Standardized entry point with validation, timing, and error handling.
        """
        start_time = time.perf_counter()
        errors = []
        result_output = {}
        success = False
        confidence = 1.0

        try:
            # 1. Validation
            validated_input = self._validate_input(input_data)
            
            # 2. Execution
            self.log_execution_step("START", {"input_summary": str(input_data)[:100]})
            result_output = self._run_logic(validated_input)
            success = result_output.get("success", True)
            confidence = result_output.get("confidence", 1.0)
            
        except ValidationError as ve:
            self.logger.error(f"Validation failed: {ve}")
            errors.append(f"Validation Error: {str(ve)}")
        except Exception as e:
            self.logger.exception(f"Execution failed: {e}")
            errors.append(f"Runtime Error: {str(e)}")
        finally:
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # 3. Telemetry & Result Construction
            final_result = KAResult(
                ka_id=self.ka_id,
                success=success,
                output=result_output.get("output", result_output) if isinstance(result_output, dict) else {},
                confidence=confidence,
                execution_time_ms=execution_time,
                errors=errors
            )
            
            self._record_telemetry(final_result)
            return final_result.model_dump()

    def _validate_input(self, input_data: Union[Dict[str, Any], BaseModel]) -> BaseModel:
        """Enforces the input_schema validation."""
        if isinstance(input_data, self.input_schema):
            return input_data
        return self.input_schema(**input_data)

    def _record_telemetry(self, result: KAResult):
        """Place holder for OpenTelemetry / Sentry reporting."""
        status = "SUCCESS" if result.success else "FAILED"
        self.logger.info(f"TELEMETRY | {self.ka_id} | {status} | {result.execution_time_ms:.2f}ms")
        
        if not result.success and len(result.errors) > 0:
            # Trigger Sentry alert if integrated
            pass

    def log_execution_step(self, step_name: str, details: Dict[str, Any] = None):
        """Standardized step logging with UTC timestamp."""
        log_msg = f"[{datetime.now(UTC).isoformat()}] {self.ka_id} | {step_name}"
        if details:
            log_msg += f" | {details}"
        self.logger.debug(log_msg)

    def calculate_confidence(self, factors: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
        """Weighted confidence calculation logic."""
        if not factors: return 0.5
        w = weights or {k: 1.0 / len(factors) for k in factors}
        total_w = sum(w.get(k, 0) for k in factors)
        if total_w == 0: return 0.5
        
        weighted_sum = sum(factors[k] * w.get(k, 0) for k in factors if k in w)
        return max(0.0, min(1.0, weighted_sum / total_w))
