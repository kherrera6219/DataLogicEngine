"""
KA-21: Persona Scaling & Committee Orchestration

This Knowledge Algorithm implements the Persona Scaling System, which extends
the base Quad Persona with dynamic pod expansion for complex, high-stakes queries.

The algorithm:
1. Evaluates if base 4 personas are sufficient (sufficiency signals)
2. If expansion needed, spawns additional personas into pods
3. Orchestrates parallel processing, synthesis, and deconfliction
4. Integrates with the DRL loop for recursive refinement

This KA runs after step 3 (Base Quad Persona) and before step 6 (Synthesis).
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Main Knowledge Algorithm Class
# =============================================================================

class KA21PersonaScaling:
    """
    KA-21: Persona Scaling & Committee Orchestration
    
    Extends the Quad Persona System with dynamic expansion for complex queries.
    
    Inputs:
        - query: Original query text
        - context: Query context from layers 1-2
        - axis_vector: 17-axis coordinate vector
        - base_persona_results: Results from base quad processing (step 3)
    
    Outputs:
        - scaling_decision: Whether to expand and how
        - orchestration_state: Complete pod processing state
        - integrated_response: Final synthesized response
        - confidence: Final confidence score
    """
    
    # Algorithm metadata
    KA_ID = "KA-21"
    KA_NAME = "Persona Scaling & Committee Orchestration"
    KA_DESCRIPTION = "Extends Quad Persona with dynamic pod expansion for complex queries"
    KA_TIER = "Persona"
    KA_LAYER = 4  # Runs in Layer 4 (after base quad position in Layer 3)
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Persona Scaling algorithm.
        
        Args:
            config: Configuration dictionary with thresholds and settings
        """
        self.config = config or {}
        
        # Lazy import to avoid circular dependencies
        self._sufficiency_tool = None
        self._pod_orchestrator = None
        
        # Metrics
        self.executions = 0
        self.expansions_triggered = 0
        self.average_confidence = 0.0
        
        logger.info(f"{self.KA_ID}: {self.KA_NAME} initialized")
    
    @property
    def sufficiency_tool(self):
        """Lazy load sufficiency tool."""
        if self._sufficiency_tool is None:
            from quad_persona.persona_scaling import PersonaSufficiencyTool
            self._sufficiency_tool = PersonaSufficiencyTool(self.config)
        return self._sufficiency_tool
    
    @property
    def pod_orchestrator(self):
        """Lazy load pod orchestrator."""
        if self._pod_orchestrator is None:
            from quad_persona.pod_orchestrator import PodOrchestrator
            self._pod_orchestrator = PodOrchestrator(self.config)
        return self._pod_orchestrator
    
    def execute(
        self,
        execution_id: str,
        params: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the persona scaling algorithm.
        
        Args:
            execution_id: Unique ID for this execution
            params: Dictionary containing:
                - query: Original query text
                - context: Query context
                - axis_vector: 17-axis coordinate vector
                - base_persona_results: Results from base quad processing
            session_id: Optional session identifier
            
        Returns:
            Dictionary with:
                - status: "completed" or "failed"
                - response: Execution results
                - confidence: Final confidence score
        """
        start_time = datetime.now(UTC)
        self.executions += 1
        
        logger.info(f"{self.KA_ID}: Starting execution {execution_id}")
        
        try:
            # Extract parameters
            query = params.get("query", "")
            context = params.get("context", {})
            axis_vector = params.get("axis_vector", {})
            base_persona_results = params.get("base_persona_results", {})
            
            if not query:
                return self._create_error_response("Missing query parameter")
            
            # Phase 1: Evaluate sufficiency
            logger.info(f"{self.KA_ID}: Evaluating persona sufficiency")
            scaling_decision = self.sufficiency_tool.evaluate(
                query=query,
                context=context,
                axis_vector=axis_vector,
                persona_results=base_persona_results
            )
            
            # Phase 2: Orchestrate if expansion needed
            orchestration_state = None
            
            if scaling_decision.should_expand:
                logger.info(f"{self.KA_ID}: Expansion triggered, orchestrating pods")
                self.expansions_triggered += 1
                
                orchestration_state = self.pod_orchestrator.orchestrate(
                    query=query,
                    context=context,
                    scaling_decision=scaling_decision,
                    base_persona_results=base_persona_results
                )
                
                final_response = orchestration_state.final_synthesis
                final_confidence = orchestration_state.final_confidence
                threshold_met = orchestration_state.threshold_met
            else:
                logger.info(f"{self.KA_ID}: Quad-only mode, using base results")
                
                # Use base persona results directly
                final_response = self._synthesize_base_results(base_persona_results)
                final_confidence = self._calculate_base_confidence(base_persona_results)
                threshold_met = final_confidence >= 0.995
            
            # Update metrics
            self._update_metrics(final_confidence)
            
            # Calculate execution time
            end_time = datetime.now(UTC)
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Build response
            response = {
                "status": "completed",
                "response": {
                    "content": final_response,
                    "scaling_mode": scaling_decision.mode,
                    "should_expand": scaling_decision.should_expand,
                    "threshold_mode": scaling_decision.threshold_mode,
                    "signals": scaling_decision.signals.to_dict(),
                    "expansion_plan": scaling_decision.expansion_plan.to_dict() if scaling_decision.expansion_plan else None,
                    "orchestration_summary": self._create_orchestration_summary(orchestration_state) if orchestration_state else None,
                    "execution_time_ms": execution_time_ms,
                    "log": f"{self.KA_ID} processed query with {'expanded committee' if scaling_decision.should_expand else 'quad-only'} mode"
                },
                "confidence": final_confidence,
                "threshold_met": threshold_met,
                "metadata": {
                    "ka_id": self.KA_ID,
                    "execution_id": execution_id,
                    "session_id": session_id,
                    "timestamp": end_time.isoformat()
                }
            }
            
            logger.info(f"{self.KA_ID}: Execution completed with confidence {final_confidence:.3f}")
            
            return response
            
        except Exception as e:
            logger.error(f"{self.KA_ID}: Execution failed: {e}")
            return self._create_error_response(str(e))
    
    def _synthesize_base_results(
        self,
        base_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """Synthesize results from base quad personas."""
        if not base_results:
            return "No base persona results available."
        
        sections = []
        sections.append("# Quad Persona Response (Base Mode)")
        
        for persona_type, result in base_results.items():
            sections.append(f"\n## {persona_type.title()} Expert")
            sections.append(result.get("response", "No response"))
            sections.append(f"*Confidence: {result.get('confidence', 0):.2f}*")
        
        return "\n".join(sections)
    
    def _calculate_base_confidence(
        self,
        base_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate confidence from base quad results."""
        if not base_results:
            return 0.5
        
        confidences = [r.get("confidence", 0.5) for r in base_results.values()]
        return sum(confidences) / len(confidences)
    
    def _create_orchestration_summary(
        self,
        state
    ) -> Dict[str, Any]:
        """Create summary of orchestration state."""
        if not state:
            return None
        
        return {
            "orchestration_id": state.orchestration_id,
            "status": state.status,
            "pods_spawned": len(state.pods),
            "total_personas": sum(p.persona_count for p in state.pods.values()),
            "conflicts_detected": len(state.cross_pod_conflicts),
            "conflicts_resolved": sum(1 for c in state.cross_pod_conflicts if c.resolved),
            "deconfliction_passes": state.deconfliction_passes,
            "final_confidence": state.final_confidence,
            "threshold_met": state.threshold_met
        }
    
    def _update_metrics(self, confidence: float):
        """Update running metrics."""
        # Update average confidence with running average
        n = self.executions
        self.average_confidence = ((n - 1) * self.average_confidence + confidence) / n
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "status": "failed",
            "response": {
                "content": f"Error: {error_message}",
                "log": f"{self.KA_ID} execution failed: {error_message}"
            },
            "confidence": 0.0,
            "threshold_met": False,
            "error": error_message
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get algorithm execution metrics."""
        return {
            "ka_id": self.KA_ID,
            "executions": self.executions,
            "expansions_triggered": self.expansions_triggered,
            "expansion_rate": self.expansions_triggered / max(1, self.executions),
            "average_confidence": self.average_confidence
        }


# =============================================================================
# Run Function (KA Entry Point)
# =============================================================================

def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Persona Scaling algorithm (KA-21).
    
    This is the standard entry point called by the KA orchestration system.
    
    Args:
        data: Dictionary containing query, context, axis_vector, and base_persona_results
        
    Returns:
        Algorithm execution results
    """
    import uuid
    
    config = data.get("config", {})
    algorithm = KA21PersonaScaling(config)
    
    execution_id = data.get("execution_id", str(uuid.uuid4()))
    session_id = data.get("session_id")
    
    return algorithm.execute(execution_id, data, session_id)


# =============================================================================
# Algorithm Registration
# =============================================================================

# Metadata for KA registry
KA_METADATA = {
    "id": "KA-21",
    "name": "Persona Scaling & Committee Orchestration",
    "description": "Extends Quad Persona System with dynamic pod expansion for complex queries",
    "tier": "Persona",
    "layer": 4,
    "version": "1.0.0",
    "author": "UKG Team",
    "inputs": ["query", "context", "axis_vector", "base_persona_results"],
    "outputs": ["scaling_decision", "orchestration_state", "integrated_response", "confidence"],
    "dependencies": ["KA-12", "KA-20"],
    "run_after": ["step3"],
    "run_before": ["step6"],
    "triggers": {
        "complexity_score": "> 60 (standard) / > 40 (high-assurance)",
        "stakes_score": "> 40 (standard) / > 30 (high-assurance)",
        "conflict_score": "> 0.2 (standard) / > 0.1 (high-assurance)",
        "coverage_score": "< 0.85 (standard) / < 0.95 (high-assurance)"
    }
}
