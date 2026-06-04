"""
Universal Knowledge Graph (UKG) System - Layer 1: Simulation Entry Layer

This module implements the Simulation Entry Layer that serves as the gateway to the 
simulation system, handling incoming queries, context wrapping, and simulation routing logic.

ENHANCED: Now integrates with Knowledge Algorithms for intelligent routing.
- KA-004: Input Validation & Normalization
- KA-005: Query Classification
- KA-036: Complexity Estimator
- KA-113: Complexity Router
"""

import logging
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Global KA Controller reference (set during initialization)
_ka_controller = None

def set_ka_controller(controller):
    """Set the global KA controller for Layer 1."""
    global _ka_controller
    _ka_controller = controller
    logger.info("Layer 1 KA Controller configured")


class LayerRouter:
    """Routes queries to the appropriate simulation layer."""
    
    def __init__(self):
        """Initialize the layer router."""
        self.layer2_handler = None
        self.configured = False
    
    def configure(self, layer2_handler):
        """Configure the router with handlers for higher layers."""
        self.layer2_handler = layer2_handler
        self.configured = True
        logger.info("LayerRouter configured with Layer 2 handler")
    
    def route_to_layer2(self, query_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route a query to Layer 2 (Knowledge Simulation)."""
        if not self.configured:
            raise RuntimeError("LayerRouter not configured with Layer 2 handler")
        
        logger.debug(f"Routing query to Layer 2: {query_payload.get('query_id', 'Unknown ID')}")
        return self.layer2_handler.simulate(query_payload)


class TriggerConditions:
    """
    Defines rules for activating higher-layer simulations.
    
    ENHANCED: Now uses KA-005 (Query Classification) and KA-036 (Complexity Estimator)
    for intelligent routing decisions.
    """
    
    @staticmethod
    def requires_simulation(query_payload: Dict[str, Any]) -> bool:
        """Determine if a query requires simulation using KA-powered analysis."""
        query_text = query_payload.get("query", "")
        
        # 1. Try KA-005: Query Classification
        if _ka_controller:
            try:
                ka005_result = _ka_controller.execute_algorithm('KA-005', {'query': query_text})
                classification = ka005_result.get('classification', {})
                if classification.get('requires_simulation'):
                    logger.info("KA-005 determined simulation required")
                    return True
                if classification.get('complexity') == 'trivial':
                    return False
            except Exception as e:
                logger.debug(f"KA-005 skipped: {e}")
        
        # 2. Try KA-036: Complexity Estimator
        if _ka_controller:
            try:
                ka036_result = _ka_controller.execute_algorithm('KA-036', {'query': query_text})
                complexity_score = ka036_result.get('complexity_score', 0.5)
                if complexity_score > 0.6:
                    logger.info(f"KA-036 complexity score {complexity_score:.2f} triggers simulation")
                    return True
            except Exception as e:
                logger.debug(f"KA-036 skipped: {e}")
        
        # 3. Fallback: Heuristic-based detection
        simulation_keywords = [
            "explain", "analyze", "compare", "evaluate", 
            "consider", "implications", "framework", "methodology"
        ]
        
        if len(query_text.split()) > 10:  # Complex query
            return True
        
        for keyword in simulation_keywords:
            if keyword in query_text.lower():
                return True
        
        return False
    
    @staticmethod
    def get_routing_tier(query_payload: Dict[str, Any]) -> str:
        """Use KA-113 to determine the optimal processing tier."""
        query_text = query_payload.get("query", "")
        
        if _ka_controller:
            try:
                ka113_result = _ka_controller.execute_algorithm('KA-113', {'query': query_text})
                tier = ka113_result.get('output', {}).get('tier', 'moderate')
                logger.info(f"KA-113 routing tier: {tier}")
                return tier
            except Exception as e:
                logger.debug(f"KA-113 skipped: {e}")
        
        # Fallback
        return 'moderate'


class SimulationEntryController:
    """
    Acts as the gateway to the simulation system.
    
    ENHANCED: Integrates KA-004 for input validation/normalization.
    """
    
    def __init__(self):
        """Initialize the simulation entry controller."""
        self.router = LayerRouter()
        self.trigger_conditions = TriggerConditions()
        logger.info("SimulationEntryController initialized with KA integration")
    
    def configure(self, layer2_handler):
        """Configure the controller with handlers for higher layers."""
        self.router.configure(layer2_handler)
        logger.info("SimulationEntryController configured")
    
    def receive_query(self, query_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Receive a query, validate it, and route it through the simulation system if needed.
        
        Args:
            query_text: The text of the query to process
            context: Optional context information for the query
            
        Returns:
            The processed query result
        """
        # Create a query payload
        query_id = str(uuid.uuid4())
        query_payload = {
            "query_id": query_id,
            "query": query_text,
            "context": context or {},
            "created_at": "",
            "session_id": context.get("session_id", "") if context else "",
        }
        
        # 1. KA-004: Input Validation & Normalization
        if _ka_controller:
            try:
                ka004_result = _ka_controller.execute_algorithm('KA-004', {'input': query_text})
                if ka004_result.get('is_valid') is False:
                    logger.warning(f"KA-004 rejected query: {ka004_result.get('reason')}")
                    return {
                        "query_id": query_id,
                        "response": "Query rejected by validation",
                        "error": ka004_result.get('reason', 'Validation failed'),
                        "success": False
                    }
                # Use normalized query if provided
                if ka004_result.get('normalized_input'):
                    query_payload['query'] = ka004_result['normalized_input']
                    query_payload['original_query'] = query_text
            except Exception as e:
                logger.debug(f"KA-004 skipped: {e}")
        
        # 2. Basic validation fallback
        validated = self.validate(query_payload)
        if not validated:
            return {
                "query_id": query_id,
                "response": "Invalid query format",
                "error": "Validation failed",
                "success": False
            }
        
        # 3. Get routing tier
        tier = self.trigger_conditions.get_routing_tier(query_payload)
        query_payload['tier'] = tier
        
        # 4. Check if simulation is required
        if self.trigger_conditions.requires_simulation(query_payload):
            logger.info(f"Simulation required for query {query_id} (tier: {tier})")
            return self.router.route_to_layer2(query_payload)
        else:
            logger.info(f"Simple query processing for {query_id} (no simulation required)")
            return {
                "query_id": query_id,
                "response": "This is a simple response without full simulation.",
                "success": True,
                "confidence": 0.7,
                "tier": tier
            }
    
    def validate(self, query_payload: Dict[str, Any]) -> bool:
        """
        Validate a query payload to ensure it has the required fields.
        """
        if "query" not in query_payload:
            logger.warning("Query payload missing 'query' field")
            return False
        
        if not isinstance(query_payload["query"], str):
            logger.warning("Query payload 'query' field is not a string")
            return False
        
        if not query_payload["query"].strip():
            logger.warning("Query payload 'query' field is empty")
            return False
        
        return True


def create_simulation_entry_controller(layer2_handler=None, ka_controller=None) -> SimulationEntryController:
    """
    Create and configure a simulation entry controller.
    
    Args:
        layer2_handler: The handler for Layer 2 simulation
        ka_controller: The KA Master Controller for intelligent routing
        
    Returns:
        A configured SimulationEntryController
    """
    if ka_controller:
        set_ka_controller(ka_controller)
    
    controller = SimulationEntryController()
    if layer2_handler:
        controller.configure(layer2_handler)
    return controller