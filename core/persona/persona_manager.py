"""
Universal Knowledge Graph (UKG) System - Persona Manager

This module provides a manager for the quad persona engine that interfaces
with the UKG chat system for enhanced response generation.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from core.persona.quad_persona_engine import QuadPersonaEngine, create_quad_persona_engine

logger = logging.getLogger(__name__)

class PersonaManager:
    """
    Manages the quad persona engine for the UKG system and provides
    an interface for generating enhanced responses.
    """
    
    def __init__(self):
        """Initialize the persona manager."""
        self.quad_persona_engine = create_quad_persona_engine()
        self.enabled = True
        logger.info("PersonaManager initialized with quad persona engine")
    
    def generate_response(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a response to a query using the quad persona engine.
        
        Args:
            query: The user query to respond to.
            context: Optional context information for the query.
            
        Returns:
            A dictionary containing the generated response and metadata.
        """
        if not self.enabled:
            return {
                "content": "Persona-based response generation is currently disabled.",
                "generated_by": "fallback",
                "confidence": 0.5
            }
        
        try:
            # Process the query through the quad persona engine
            result = self.quad_persona_engine.process_query(query)
            
            # Extract the response content
            response_content = result["response"]["content"]
            
            # Return the response with metadata
            return {
                "content": response_content,
                "generated_by": "quad_persona_engine",
                "active_personas": result["response"].get("active_personas", []),
                "confidence": result["response"].get("confidence", 0.7),
                "full_result": result
            }
        except Exception as e:
            logger.error(f"Error generating persona-based response: {str(e)}")
            return {
                "content": f"I encountered an error while processing your query through the universal knowledge graph: {str(e)}",
                "generated_by": "error_handler",
                "confidence": 0.3
            }
    
    def enable(self):
        """Enable the persona manager."""
        self.enabled = True
        logger.info("PersonaManager enabled")
    
    def disable(self):
        """Disable the persona manager."""
        self.enabled = False
        logger.info("PersonaManager disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the persona manager."""
        return {
            "enabled": self.enabled,
            "engine_status": "initialized" if self.quad_persona_engine else "not_initialized"
        }
    
    def get_persona_types(self) -> List[str]:
        """Get the list of available persona types."""
        return self.quad_persona_engine.PERSONA_TYPES
    
    def get_persona_details(self, persona_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the details of a specific persona.
        
        Args:
            persona_type: The type of persona to get details for.
            
        Returns:
            A dictionary containing the persona details, or None if not found.
        """
        persona = self.quad_persona_engine.get_persona(persona_type)
        if persona:
            return persona.to_dict()
        return None

# Singleton instance for global access
_persona_manager_instance = None

def get_persona_manager() -> PersonaManager:
    """Get the singleton instance of the persona manager."""
    global _persona_manager_instance
    if _persona_manager_instance is None:
        _persona_manager_instance = PersonaManager()
    return _persona_manager_instance