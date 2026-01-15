"""
KA-012: Persona Simulation
Purpose: Run expert personas (knowledge/sector/regulatory/compliance).
"""
import logging
from typing import Dict, List, Any, Optional
import time
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA012PersonaSimulation(KnowledgeAlgorithm):
    """
    KA-012: Orchestrates the simulation of multiple expert personas.
    Formerly KA-20 in Legacy system.
    """
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.personas = self._initialize_personas()
        
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the Quad Persona simulation for a given query.
        """
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        if not query:
            return {
                "ka_id": "KA-012",
                "error": "No query provided",
                "success": False
            }
        
        self.log_execution_step("Orchestrating Personas", {"query": query})

        # Determine which personas to activate based on context
        active_personas = self._determine_active_personas(query, context)
        
        # Process the query through each active persona
        persona_results = {}
        execution_order = []
        
        for persona_type in active_personas:
            start_time = time.time()
            
            # Get persona-specific results
            result = self._process_with_persona(persona_type, query, context)
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            
            persona_results[persona_type] = {
                **result,
                "processing_time_ms": processing_time
            }
            
            execution_order.append(persona_type)
        
        # Integrate results from all personas
        integrated_result = self._integrate_results(persona_results, query, context)
        
        return {
            "ka_id": "KA-012",
            "ka_name": "Persona Simulation",
            "query": query,
            "active_personas": active_personas,
            "execution_order": execution_order,
            "persona_results": persona_results,
            "integrated_result": integrated_result,
            "confidence": self._calculate_overall_confidence(persona_results),
            "success": True
        }

    def _initialize_personas(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the four expert personas with their characteristics."""
        return {
            "knowledge": {
                "name": "Knowledge Expert",
                "description": "Provides theoretical frameworks, academic perspectives, and conceptual models",
                "axis": 8,
                "expertise_level": 0.9,
                "focus_areas": ["theory", "research", "frameworks", "concepts", "models", "principles"],
                "analysis_style": "comprehensive",
                "tone": "academic"
            },
            "sector": {
                "name": "Sector Expert",
                "description": "Offers industry-specific insights, market dynamics, and practical applications",
                "axis": 9,
                "expertise_level": 0.9,
                "focus_areas": ["industry", "market", "practical", "implementation", "business", "operational"],
                "analysis_style": "practical",
                "tone": "professional"
            },
            "regulatory": {
                "name": "Regulatory Expert",
                "description": "Addresses legal requirements, governance frameworks, and policy mandates",
                "axis": 10,
                "expertise_level": 0.85,
                "focus_areas": ["legal", "regulation", "compliance", "governance", "policy", "requirements"],
                "analysis_style": "structured",
                "tone": "formal"
            },
            "compliance": {
                "name": "Compliance Expert",
                "description": "Focuses on standards adherence, verification protocols, and certification requirements",
                "axis": 11,
                "expertise_level": 0.85,
                "focus_areas": ["standards", "verification", "certification", "audit", "controls", "documentation"],
                "analysis_style": "detailed",
                "tone": "authoritative"
            }
        }
        
    def _determine_active_personas(self, query: str, context: Dict[str, Any]) -> List[str]:
        if "personas" in context:
            requested = context["personas"]
            if isinstance(requested, list):
                valid = [p for p in requested if p in self.personas]
                if valid: return valid
        
        # Keyword based (simplified from legacy)
        return ["knowledge", "sector", "regulatory", "compliance"]

    def _process_with_persona(self, persona_type: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        persona = self.personas.get(persona_type, {})
        if not persona:
            return {"error": f"Unknown {persona_type}", "success": False}
            
        domain = context.get("domain", "general")
        
        # Simple simulated response logic
        response = f"From a {persona['name']} perspective on '{query}': Analysis in {domain} domain."
        
        return {
            "persona_type": persona_type,
            "name": persona["name"],
            "response": response,
            "confidence": 0.85,
            "success": True
        }

    def _integrate_results(self, persona_results: Dict[str, Any], query: str, context: Dict[str, Any]) -> str:
        return "Integrated analysis from active personas."

    def _calculate_overall_confidence(self, persona_results: Dict[str, Any]) -> float:
        return 0.9

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA012PersonaSimulation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-012 Failed: {e}")
        return {"success": False, "error": str(e)}
