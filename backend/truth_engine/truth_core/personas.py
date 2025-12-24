"""
TruthCore Persona Enhancement

Extends QuadPersonaEngine with multi-persona reasoning.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class PersonaEnhancer:
    """
    Enhances persona-based reasoning with TruthCore capabilities.
    
    Adds:
    - Analyst: Data-driven analysis
    - Expert: Domain expertise
    - Critic: Critical evaluation
    - Synthesizer: Integration and synthesis
    """
    
    TRUTH_PERSONAS = {
        'analyst': {
            'role': 'Data Analyst',
            'focus': 'Quantitative analysis and pattern recognition',
            'system_prompt': 'You are an expert data analyst. Focus on facts, statistics, and evidence-based reasoning.',
            'weight': 0.25
        },
        'expert': {
            'role': 'Domain Expert',
            'focus': 'Deep domain knowledge and expertise',
            'system_prompt': 'You are a domain expert. Provide authoritative insights based on deep knowledge.',
            'weight': 0.30
        },
        'critic': {
            'role': 'Critical Evaluator',
            'focus': 'Finding flaws, risks, and counterarguments',
            'system_prompt': 'You are a critical evaluator. Identify weaknesses, risks, and alternative perspectives.',
            'weight': 0.20
        },
        'synthesizer': {
            'role': 'Knowledge Synthesizer',
            'focus': 'Integration and holistic understanding',
            'system_prompt': 'You are a synthesizer. Integrate multiple perspectives into coherent insights.',
            'weight': 0.25
        }
    }

    def __init__(self, quad_persona_engine=None):
        """Initialize with optional QuadPersonaEngine integration."""
        self.quad_persona_engine = quad_persona_engine
        self.active_personas = {}
        logger.info("PersonaEnhancer initialized")

    def enhance_query(self, query: str, context: Dict[str, Any] = None,
                      personas: List[str] = None) -> Dict[str, Any]:
        """
        Enhance query processing with multi-persona reasoning.
        
        Each persona provides a different perspective on the query.
        """
        context = context or {}
        personas = personas or list(self.TRUTH_PERSONAS.keys())
        
        persona_responses = {}
        weights = {}
        
        for persona_name in personas:
            if persona_name not in self.TRUTH_PERSONAS:
                continue
            
            persona_config = self.TRUTH_PERSONAS[persona_name]
            response = self._get_persona_response(persona_name, persona_config, query, context)
            persona_responses[persona_name] = response
            weights[persona_name] = persona_config['weight']
        
        synthesized = self._synthesize_responses(persona_responses, weights)
        
        return {
            'enhanced_query': query,
            'persona_responses': persona_responses,
            'weights': weights,
            'synthesized_response': synthesized,
            'personas_used': personas,
            'timestamp': datetime.now(UTC).isoformat()
        }

    def _get_persona_response(self, persona_name: str, persona_config: Dict[str, Any],
                               query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get response from a specific persona."""
        if self.quad_persona_engine:
            try:
                result = self.quad_persona_engine.process_with_persona(
                    query, persona_name, context
                )
                return {
                    'persona': persona_name,
                    'role': persona_config['role'],
                    'response': result.get('response', ''),
                    'confidence': result.get('confidence', 0.8),
                    'source': 'quad_persona_engine'
                }
            except Exception as e:
                logger.warning(f"QuadPersonaEngine failed for {persona_name}: {e}")
        
        return {
            'persona': persona_name,
            'role': persona_config['role'],
            'focus': persona_config['focus'],
            'response': f"[{persona_config['role']}] Analysis of: {query[:100]}...",
            'confidence': 0.75,
            'source': 'default'
        }

    def _synthesize_responses(self, responses: Dict[str, Dict[str, Any]],
                               weights: Dict[str, float]) -> Dict[str, Any]:
        """Synthesize multiple persona responses into unified result."""
        if not responses:
            return {'content': '', 'confidence': 0}
        
        weighted_confidence = sum(
            responses[p].get('confidence', 0) * weights.get(p, 0.25)
            for p in responses
        )
        
        perspectives = [
            f"**{responses[p]['role']}**: {responses[p].get('focus', '')}"
            for p in responses
        ]
        
        return {
            'content': '\n'.join(perspectives),
            'confidence': min(weighted_confidence, 1.0),
            'persona_count': len(responses),
            'synthesis_method': 'weighted_integration'
        }

    def get_persona_info(self, persona: str = None) -> Dict[str, Any]:
        """Get information about personas."""
        if persona:
            return self.TRUTH_PERSONAS.get(persona, {})
        return self.TRUTH_PERSONAS

    def map_to_axis(self, persona: str) -> int:
        """Map persona to UKG axis number."""
        axis_mapping = {
            'analyst': 8,
            'expert': 9,
            'critic': 10,
            'synthesizer': 11
        }
        return axis_mapping.get(persona, 8)
