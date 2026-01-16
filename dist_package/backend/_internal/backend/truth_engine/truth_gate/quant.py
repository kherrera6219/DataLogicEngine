from typing import Dict, List, Any, Optional
import logging
from backend.truth_engine.truth_gate.schemas import Layer6Input, QuantBundle
from backend.truth_engine.truth_gate.quant_backends.statistical import StatisticalBackend
from backend.truth_engine.truth_gate.quant_backends.logical import LogicalBackend

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

    def validate(self, draft_solution: str, claims: List[str], data_context: Optional[Dict[str, Any]] = None) -> QuantBundle:
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
                validation_flags=[f"Input Schema Error: {str(e)}"]
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
                ka039_result = self.ka_controller.execute_algorithm('KA-039', {'data': input_payload.data_context})
                if ka039_result.get('anomalies'):
                    anomalies.extend(ka039_result['anomalies'])
                    total_risk += 0.1
            except Exception as e:
                logger.debug(f"KA-039 skipped: {e}")
        
        # 4. KA-116: Entropy Detection (Supplementary)
        if self.ka_controller:
            try:
                ka116_result = self.ka_controller.execute_algorithm('KA-116', {'claims': input_payload.claims})
                if ka116_result.get('high_entropy_claims'):
                    for hec in ka116_result['high_entropy_claims']:
                        validation_flags.append(f"High Entropy Claim: {hec}")
                    total_risk += 0.15
            except Exception as e:
                logger.debug(f"KA-116 skipped: {e}")
                    
        # 5. Final Synthesis
        avg_confidence = sum(confidence_map.values()) / len(confidence_map) if confidence_map else 0.0
        normalized_risk = min(1.0, total_risk)
        
        # Thresholds: Risk < 0.7 and Confidence > 0.6
        is_valid = normalized_risk < 0.7 and (avg_confidence > 0.6 or not confidence_map)
        
        return QuantBundle(
            is_valid=is_valid,
            risk_score=normalized_risk,
            confidence_map=confidence_map,
            anomalies=anomalies,
            validation_flags=validation_flags
        )
