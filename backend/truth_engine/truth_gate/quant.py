import logging
from typing import Any

from backend.knowledge_algorithms.consumer import (
    execute_required_ka,
    require_output_field,
)
from backend.truth_engine.truth_gate.quant_backends.logical import LogicalBackend
from backend.truth_engine.truth_gate.quant_backends.statistical import (
    StatisticalBackend,
)
from backend.truth_engine.truth_gate.schemas import Layer6Input, QuantBundle

logger = logging.getLogger(__name__)

class QuantValidationService:
    """
    Layer 6: Quantitative Validation Service.
    Orchestrates Logical and Statistical backends to verify claims.
    """
    
    def __init__(self, ka_controller=None):
        self.ka_controller = ka_controller
        self.stat_backend = StatisticalBackend()
        self.logic_backend = LogicalBackend()
        logger.info("QuantValidationService (Layer 6) initialized with modular backends")

    @staticmethod
    def _numeric_data_points(data_context: dict[str, Any] | None) -> list[float]:
        points: list[float] = []

        def collect(value: Any) -> None:
            if isinstance(value, bool):
                return
            if isinstance(value, (int, float)):
                points.append(float(value))
            elif isinstance(value, dict):
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    collect(nested)

        collect(data_context or {})
        return points

    def validate(self, draft_solution: str, claims: list[str], data_context: dict[str, Any] | None = None) -> QuantBundle:
        """
        Main entry point for Layer 6 validation.
        """
        # Validate Input Schema
        try:
            input_payload = Layer6Input(
                draft_solution=draft_solution,
                claims=claims,
                data_context=data_context
            )
        except ValueError as e:
            logger.error(f"Layer 6 Input Validation Failed: {e}")
            # Fail closed or return default risk
            return QuantBundle(
                is_valid=False,
                risk_score=1.0, 
                confidence_map={}, 
                anomalies=[], 
                validation_flags=[f"Input Schema Error: {e!s}"]
            )

        anomalies = []
        validation_flags = []
        total_risk = 0.0
        
        # 1. Logical Backend (Text Claims)
        confidence_map = self.logic_backend.score_claims(input_payload.claims)
        
        for cid, score in confidence_map.items():
            if score < 0.5:
                # Find original claim text roughly
                idx = int(cid.split('_')[1])
                claim_text = input_payload.claims[idx]
                validation_flags.append(f"Low Confidence Claim: '{claim_text[:50]}...' ({score:.2f})")
                total_risk += 0.2

        # 2. Statistical Backend (Data Context)
        if input_payload.data_context and 'tables' in input_payload.data_context:
            for table_name, table_data in input_payload.data_context['tables'].items():
                table_risks = self.stat_backend.analyze_table(table_name, table_data)
                anomalies.extend(table_risks)
                if table_risks:
                    total_risk += 0.3
        
        # 3. KA-039: Anomaly Detection (Supplementary)
        if self.ka_controller:
            try:
                ka039_result = execute_required_ka(
                    self.ka_controller,
                    "KA-039",
                    {"data": self._numeric_data_points(input_payload.data_context)},
                )
                ka039_anomalies = require_output_field(
                    ka039_result,
                    "anomalies",
                )
                if ka039_anomalies:
                    anomalies.extend(ka039_anomalies)
                    total_risk += 0.1
            except Exception as exc:
                validation_flags.append("KA-039 anomaly validation failed")
                total_risk += 0.2
                logger.warning("KA-039 anomaly validation failed: %s", exc)
        
        # 4. KA-116: Entropy Detection (Supplementary)
        if self.ka_controller:
            try:
                ka116_result = execute_required_ka(
                    self.ka_controller,
                    "KA-116",
                    {"claims": input_payload.claims},
                )
                entropy_state = require_output_field(ka116_result, "state")
                entropy_score = float(
                    require_output_field(ka116_result, "entropy_score")
                )
                if entropy_state == "CRITICAL":
                    validation_flags.append(
                        f"High aggregate claim entropy: {entropy_score:.3f}"
                    )
                    total_risk += 0.15
            except Exception as exc:
                validation_flags.append("KA-116 entropy validation failed")
                total_risk += 0.2
                logger.warning("KA-116 entropy validation failed: %s", exc)
                    
        # 5. Final Synthesis
        avg_confidence = sum(confidence_map.values()) / len(confidence_map) if confidence_map else 0.0
        normalized_risk = min(1.0, total_risk)
        
        # Thresholds: Risk < 0.7 and Confidence > 0.6
        is_valid = (
            normalized_risk < 0.7
            and bool(confidence_map)
            and avg_confidence > 0.6
        )
        
        return QuantBundle(
            is_valid=is_valid,
            risk_score=normalized_risk,
            confidence_map=confidence_map,
            anomalies=anomalies,
            validation_flags=validation_flags
        )
