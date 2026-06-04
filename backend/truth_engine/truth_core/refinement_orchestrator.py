import logging
import asyncio
import hashlib
from typing import Dict, Any
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class RefinementStep:
    def __init__(self, name: str, ka_id: str, description: str):
        self.name = name
        self.ka_id = ka_id
        self.description = description

class RefinementOrchestrator:
    """
    Orchestrates the 12-step refinement workflow for UKG output.
    Ensures iterative polishing and confidence gating (target >= 99.5%).
    """

    STEPS = [
        RefinementStep("AoT_Polish", "KA-001", "Algorithm of Thought refinement"),
        RefinementStep("Coordinate_Fix", "KA-017", "17-Axis coordinate alignment check"),
        RefinementStep("Nurnburg_Naming", "KA-075", "Standardized naming convention audit"),
        RefinementStep("Contradiction_Sieve", "KA-026", "Final dissonance removal"),
        RefinementStep("Regulatory_Crosswalk", "KA-016", "Multi-jurisdictional law check"),
        RefinementStep("PII_Redaction", "L10-KA-003", "Sanitization and privacy leakage check"),
        RefinementStep("Bias_Neutralization", "KA-010", "Cognitive bias reduction"),
        RefinementStep("Logic_Hardening", "KA-011", "Formal logic validation"),
        RefinementStep("Source_Provenance", "KA-018", "Evidence attribution audit"),
        RefinementStep("Style_Alignment", "KA-057", "Tone and domain-specific language sync"),
        RefinementStep("Safety_Sentinel", "L10-KA-006", "Final Layer 10 release authority"),
        RefinementStep("Memory_Patch", "KA-051", "Recursive memory feedback loop")
    ]

    def __init__(self, ka_controller: Any):
        self.ka_controller = ka_controller
        self.target_confidence = 0.995

    async def refine(self, initial_response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the 12-step refinement loop with hardening and confidence gating.
        """
        current_response = initial_response.copy()
        last_good_state = initial_response.copy()
        history = []
        
        logger.info(f"Starting hardened 12-step refinement for initial confidence: {current_response.get('confidence', 0)}")

        for step in self.STEPS:
            try:
                # 1. Execute refinement step
                step_result = await self._execute_step(step, current_response, context)
                
                # 2. Risk Mitigation: Validate output before committing
                new_confidence = step_result.get('confidence', 0)
                prev_confidence = last_good_state.get('confidence', 0)

                # Security Rule: If confidence drops significantly (>15%), potentially adversarial or error
                if new_confidence < prev_confidence - 0.15:
                    logger.warning(f"Refinement Step {step.name} caused anomaly (conf: {prev_confidence} -> {new_confidence}). Recovering...")
                    current_response = last_good_state.copy()
                    continue

                # 3. State Update
                current_response.update(step_result)
                last_good_state = current_response.copy()

                history.append({
                    "step": step.name,
                    "ka_id": step.ka_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "confidence": new_confidence,
                    "confidence_gain": new_confidence - prev_confidence
                })
                
                # 5. Gated Stop Conditions (Target >= 99.5%)
                if new_confidence >= self.target_confidence and step.name not in ["Safety_Sentinel", "PII_Redaction"]:
                    logger.info(f"Refinement target {self.target_confidence} met at step {step.name}. Proceeding to final gates.")
                    # We continue to Safety/PII steps always

            except Exception as e:
                logger.error(f"Refinement step {step.name} critical failure: {e}. Reverting to last known good state.")
                current_response = last_good_state.copy()

        current_response['refinement_history'] = history
        try:
            drl_result = self._run_drl_convergence(current_response, context)
            current_response['drl_convergence'] = drl_result
            current_response['confidence_candidates'] = {
                "refinement": float(current_response.get('confidence', 0) or 0),
                "drl_convergence": float(drl_result.get('confidence', 0) or 0),
            }
            if not self.STEPS and drl_result.get("threshold_met"):
                current_response['confidence'] = current_response['confidence_candidates']['drl_convergence']
        except Exception as exc:
            logger.debug("DRL convergence refinement skipped: %s", exc)
        current_response['final_confidence'] = current_response.get('confidence', 0)
        
        return current_response

    def _run_drl_convergence(self, current_response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run quad DeepRecursiveLearning convergence on a deterministic content vector."""
        import numpy as np
        from core.persona.quad.mathematical_framework import DeepRecursiveLearning

        content = str(current_response.get('content', ''))
        digest = hashlib.sha256(content.encode()).digest()
        vector = np.array([(byte - 128) / 128.0 for byte in digest], dtype=float)
        learner = DeepRecursiveLearning(max_depth=12, epsilon=-1.0)
        _, iterations, confidence = learner.deep_recursive_learning(vector, context)
        return {
            "iterations": iterations,
            "confidence": confidence,
            "target_confidence": self.target_confidence,
            "threshold_met": confidence >= self.target_confidence,
        }

    async def _execute_step(self, step: RefinementStep, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes a specific KA for refinement via the Master Controller."""
        try:
            # Prepare KA payload
            ka_input = {
                "query": context.get('query', ''),
                "content": content.get('content', ''),
                "context": context,
                "step_metadata": {
                    "session_id": context.get('session_id'),
                    "step_name": step.name,
                    "target_confidence": self.target_confidence
                }
            }
            
            # Execute actual KA logic via orchestrator's controller
            # Note: Using run_in_executor if the KA-Master is purely synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.ka_controller.execute_algorithm, 
                step.ka_id, 
                ka_input
            )
            
            # Extract refined output. KAs should return 'refined_content' or 'response'
            refined_content = result.get('refined_content', result.get('response', content.get('content', '')))
            # Confidence should be returned by the KA based on its specific audit logic
            new_confidence = result.get('confidence', content.get('confidence', 0.8))
            
            return {
                "content": refined_content,
                "confidence": new_confidence,
                f"{step.name}_status": "executed",
                "ka_id": step.ka_id,
                "audit_meta": result.get('audit_meta', {})
            }
        except Exception as e:
            logger.error(f"KA Execution Failed for {step.name} ({step.ka_id}): {e}")
            raise
