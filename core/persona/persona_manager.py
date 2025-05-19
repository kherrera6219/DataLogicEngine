"""
Universal Knowledge Graph (UKG) System - Persona Manager

This module provides a manager for the quad persona engine that interfaces
with the UKG chat system for enhanced response generation, with integrated
memory management for improved contextual awareness.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple

from core.persona.quad_persona_engine import QuadPersonaEngine, create_quad_persona_engine
from core.persona.memory_system import get_memory_manager, MemoryManager

logger = logging.getLogger(__name__)

class PersonaManager:
    """
    Manages the quad persona engine for the UKG system and provides
    an interface for generating enhanced responses with memory integration.
    """
    
    def __init__(self):
        """Initialize the persona manager."""
        self.quad_persona_engine = create_quad_persona_engine()
        self.memory_manager = get_memory_manager()
        self.enabled = True
        self.use_memory = True
        logger.info("PersonaManager initialized with quad persona engine and memory system")
    
    def generate_response(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a response to a query using the quad persona engine with memory integration.
        
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
            # Initialize context if not provided
            context = context or {}
            
            # Retrieve relevant memories if memory is enabled
            memories = {}
            if self.use_memory:
                # Find memories relevant to this query
                memories = self.retrieve_relevant_memories(query, context)
                logger.info(f"Retrieved {sum(len(mems) for mems in memories.values())} memories across {len(memories)} contexts")
            
            # Prepare query context with memories
            query_context = self.prepare_query_context(query, context, memories)
            
            # Process the query through the quad persona engine
            result = self.quad_persona_engine.process_query(query)
            
            # Extract the response content
            response_content = result["response"]["content"]
            
            # Store insights from persona responses if memory is enabled
            if self.use_memory:
                self.store_insights(query, result["persona_responses"])
            
            # Return the response with metadata
            return {
                "content": response_content,
                "generated_by": "quad_persona_engine",
                "active_personas": result["response"].get("active_personas", []),
                "confidence": result["response"].get("confidence", 0.7),
                "used_memories": bool(memories),
                "memory_contexts": list(memories.keys()) if memories else [],
                "full_result": result
            }
        except Exception as e:
            logger.error(f"Error generating persona-based response: {str(e)}")
            return {
                "content": f"I encountered an error while processing your query through the universal knowledge graph: {str(e)}",
                "generated_by": "error_handler",
                "confidence": 0.3
            }
    
    def retrieve_relevant_memories(self, query: str, context: Dict[str, Any]) -> Dict[str, List[Any]]:
        """
        Retrieve memories relevant to the current query.
        
        Args:
            query: The user query
            context: Context information for the query
            
        Returns:
            A dictionary mapping context names to relevant memories
        """
        # Determine which memory contexts to search based on the query
        context_names = [
            "general",
            "knowledge_expert",
            "sector_expert",
            "regulatory_expert",
            "compliance_expert"
        ]
        
        # If we have a conversation ID in the context, create a conversation-specific context
        conversation_id = context.get("conversation_id")
        if conversation_id:
            context_name = f"conversation_{conversation_id}"
            self.memory_manager.create_context(context_name, "conversation", {
                "conversation_id": conversation_id
            })
            context_names.append(context_name)
        
        # Find relevant memories
        memories = self.memory_manager.find_relevant_memories(query, context_names)
        return memories
    
    def prepare_query_context(self, query: str, context: Dict[str, Any], 
                            memories: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Prepare a query context with relevant memories for the quad persona engine.
        
        Args:
            query: The user query
            context: The original context
            memories: Retrieved memories relevant to the query
            
        Returns:
            An enhanced context with memories
        """
        enhanced_context = context.copy()
        
        # Add memories to the context
        if memories:
            memory_context = {}
            for context_name, memory_list in memories.items():
                memory_context[context_name] = [memory.to_dict() for memory in memory_list]
            enhanced_context["memories"] = memory_context
        
        # Add working memory
        working_memory = self.memory_manager.get_working_memory(5)  # Last 5 items
        if working_memory:
            enhanced_context["working_memory"] = working_memory
        
        return enhanced_context
    
    def store_insights(self, query: str, persona_responses: Dict[str, Dict[str, Any]]):
        """
        Store insights from persona responses in memory.
        
        Args:
            query: The original query
            persona_responses: Responses from the different personas
        """
        self.memory_manager.extract_insights(query, persona_responses)
        
        # Store the query itself in general memory
        self.memory_manager.add_memory(
            content=query,
            memory_type="query",
            source="user",
            context_name="general",
            metadata={"timestamp": str(datetime.utcnow())}
        )
    
    def enable(self):
        """Enable the persona manager."""
        self.enabled = True
        logger.info("PersonaManager enabled")
    
    def disable(self):
        """Disable the persona manager."""
        self.enabled = False
        logger.info("PersonaManager disabled")
    
    def enable_memory(self):
        """Enable memory usage."""
        self.use_memory = True
        logger.info("Memory system enabled")
    
    def disable_memory(self):
        """Disable memory usage."""
        self.use_memory = False
        logger.info("Memory system disabled")
    
    def clear_working_memory(self):
        """Clear the working memory."""
        self.memory_manager.clear_working_memory()
        logger.info("Working memory cleared")
    
    def add_memory(self, content: str, memory_type: str, source: str, 
                 context_name: str = "general", metadata: Dict[str, Any] = None) -> bool:
        """
        Add a memory entry to a specific context.
        
        Args:
            content: The content of the memory
            memory_type: The type of memory (e.g., "fact", "insight")
            source: The source of the memory (e.g., "user", "system")
            context_name: The name of the context to add the memory to
            metadata: Additional metadata for the memory
            
        Returns:
            True if the memory was added successfully, False otherwise
        """
        memory = self.memory_manager.add_memory(content, memory_type, source, context_name, metadata)
        return memory is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the persona manager."""
        memory_contexts = {name: len(context.memories) for name, context in self.memory_manager.contexts.items()}
        return {
            "enabled": self.enabled,
            "use_memory": self.use_memory,
            "engine_status": "initialized" if self.quad_persona_engine else "not_initialized",
            "memory_contexts": memory_contexts,
            "working_memory_size": len(self.memory_manager.get_working_memory())
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

# Add the missing import
from datetime import datetime

# Singleton instance for global access
_persona_manager_instance = None

def get_persona_manager() -> PersonaManager:
    """Get the singleton instance of the persona manager."""
    global _persona_manager_instance
    if _persona_manager_instance is None:
        _persona_manager_instance = PersonaManager()
    return _persona_manager_instance