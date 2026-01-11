"""
Universal Knowledge Graph (UKG) System - Simulation Engine

This module integrates the quad persona components and memory management
to create a complete simulation engine for the UKG system.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC

from quad_persona.quad_engine import QuadPersonaEngine, create_quad_persona_engine
from quad_persona.persona_loader import PersonaLoader
from quad_persona.axis_role_mapper import AxisRoleMapper
from simulation.memory_manager import MemoryManager
from simulation.refinement_workflow import RefinementWorkflow, create_refinement_workflow

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    The Simulation Engine orchestrates the quad persona simulation,
    memory management, and refinement workflow for the UKG system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the simulation engine.
        
        Args:
            config: Configuration for the engine
        """
        self.config = config or {}
        
        # Initialize components
        try:
            self.quad_persona_engine = QuadPersonaEngine()
        except TypeError:
            self.quad_persona_engine = create_quad_persona_engine()
        self.persona_loader = PersonaLoader()
        self.axis_mapper = AxisRoleMapper()
        self.memory_manager = MemoryManager()
        self.refinement_workflow = create_refinement_workflow()
        
        logger.info("Simulation Engine initialized with all components")
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query through the simulation engine.
        
        This method:
        1. Prepares the query context with relevant memories
        2. Maps the query to appropriate personas via the axis system
        3. Processes the query through the quad persona engine
        4. Applies the refinement workflow for recursive improvements
        5. Stores insights in memory for future reference
        
        Args:
            query: The query to process
            context: Additional context for the query
            
        Returns:
            The processing result, including the final response
        """
        start_time = datetime.now(UTC)
        context = context or {}
        
        # Track simulation
        simulation_id = context.get('simulation_id', f"sim_{datetime.now(UTC).isoformat()}")
        
        # Initialize result structure
        result = {
            'simulation_id': simulation_id,
            'query': query,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'status': 'processing',
            'response': None,
            'confidence': 0.0,
            'processing_metadata': {}
        }
        
        try:
            # Step 1: Enhance context with memories
            conversation_id = context.get('conversation_id')
            enhanced_context = self._prepare_memory_context(query, conversation_id)
            
            # Add original context
            for key, value in context.items():
                if key not in enhanced_context:
                    enhanced_context[key] = value
            
            # Log context preparation
            result['processing_metadata']['memory_context'] = {
                'memory_streams_used': list(enhanced_context.get('memories', {}).keys()),
                'working_memory_size': len(enhanced_context.get('working_memory', [])),
                'timestamp': datetime.now(UTC).isoformat()
            }
            
            # Step 2: Map query to personas via axis system
            axis_context = self._map_query_to_axis_context(query, enhanced_context)
            result['processing_metadata']['axis_context'] = axis_context
            
            # Step 3: Process through quad persona engine
            persona_result = self.quad_persona_engine.process_query(query)
            
            # Extract confidence from persona results (avg of all personas)
            confidence = persona_result.get('confidence', 0.7) if isinstance(persona_result, dict) else 0.7
            logger.debug(f"Persona confidence extracted: {confidence}")
            
            # Extract active personas from perspectives and build synthesized response
            active_personas = []
            persona_results_for_refinement = {}
            perspective_texts = []
            
            if isinstance(persona_result, dict) and 'perspectives' in persona_result:
                for perspective in persona_result.get('perspectives', []):
                    persona_name = perspective.get('persona', '').lower().replace(' ', '_')
                    persona_conf = perspective.get('confidence', 0.7)
                    perspective_text = perspective.get('perspective', '')
                    
                    active_personas.append(persona_name)
                    perspective_texts.append(f"[{perspective.get('persona', 'Expert')}]: {perspective_text}")
                    
                    # Format for refinement workflow's _assess_confidence
                    persona_results_for_refinement[persona_name] = {
                        'confidence': persona_conf,
                        'perspective': perspective_text,
                        'name': perspective.get('persona', '')
                    }
                    logger.debug(f"Persona {persona_name} confidence: {persona_conf}")
            
            if not active_personas:
                active_personas = ["knowledge", "sector", "regulatory", "compliance"]
            
            # Build synthesized response content from perspectives
            if perspective_texts:
                response_content = "\n\n".join(perspective_texts)
            else:
                response_content = str(persona_result)
            
            # Step 4: Apply refinement workflow with persona results
            refinement_context = {
                'query': query,
                'response': response_content,
                'active_personas': active_personas,
                'confidence': confidence,
                'axis_context': axis_context,
                'persona_results': persona_results_for_refinement  # For _assess_confidence
            }
            
            refined_result = self.refinement_workflow.execute_workflow(refinement_context)
            
            # Extract final response and confidence
            final_response = refined_result.get('final_response', response_content)
            if isinstance(final_response, dict):
                final_response = final_response.get('content', response_content)
            final_confidence = refined_result.get('final_confidence', confidence)
            
            # Step 5: Store insights in memory
            if conversation_id:
                # Ensure conversation memory stream exists
                self.memory_manager.create_conversation_memory(conversation_id, {
                    'conversation_id': conversation_id,
                    'last_query': query,
                    'last_updated': datetime.now(UTC).isoformat()
                })
                
                # Add user query to conversation memory
                self.memory_manager.add_conversation_memory(
                    conversation_id=conversation_id,
                    role='user',
                    content=query,
                    metadata={'timestamp': datetime.now(UTC).isoformat()}
                )
                
                # Add system response to conversation memory
                self.memory_manager.add_conversation_memory(
                    conversation_id=conversation_id,
                    role='system',
                    content=final_response,
                    metadata={
                        'timestamp': datetime.now(UTC).isoformat(),
                        'confidence': final_confidence,
                        'active_personas': active_personas
                    }
                )
            
            # Extract insights from persona responses
            persona_responses = {}
            # In real implementation, extract from persona_result
            
            # Store persona insights in memory
            self.memory_manager.extract_insights(query, final_response, persona_responses)
            
            # Save memories to storage
            self.memory_manager.save_memories()
            
            # Complete result
            end_time = datetime.now(UTC)
            result.update({
                'end_time': end_time.isoformat(),
                'status': 'completed',
                'response': final_response,
                'confidence': final_confidence,
                'active_personas': active_personas,
                'processing_time_ms': (end_time - start_time).total_seconds() * 1000
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            
            # Complete result with error
            end_time = datetime.now(UTC)
            result.update({
                'end_time': end_time.isoformat(),
                'status': 'error',
                'error': str(e),
                'processing_time_ms': (end_time - start_time).total_seconds() * 1000
            })
            
            return result
    
    def _prepare_memory_context(self, query: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Prepare memory context for a query.
        
        Args:
            query: The query to prepare context for
            conversation_id: Optional conversation ID
            
        Returns:
            Memory context for the query
        """
        return self.memory_manager.generate_memory_context(query, conversation_id)
    
    def _map_query_to_axis_context(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a query to the 13-axis context.
        
        Args:
            query: The query to map
            context: Additional context
            
        Returns:
            Axis context for the query
        """
        # In a real implementation, this would analyze the query and map to axes
        # For now, use placeholder values
        axis_context = {
            'axis_coordinates': {
                '1': 0.5,  # Knowledge & Cognitive Framework
                '2': 0.3,  # Sectors
                '3': 0.3,  # Domains
                '8': 0.8,  # Knowledge Expert
                '9': 0.6,  # Sector Expert
                '10': 0.4,  # Regulatory Expert
                '11': 0.4   # Compliance Expert
            },
            'domain': context.get('domain'),
            'sector': context.get('sector'),
            'pillar_level': context.get('pillar_level')
        }
        
        return axis_context


# Factory function to create a simulation engine
def create_simulation_engine(config: Dict[str, Any] = None) -> SimulationEngine:
    """Create a simulation engine."""
    return SimulationEngine(config)