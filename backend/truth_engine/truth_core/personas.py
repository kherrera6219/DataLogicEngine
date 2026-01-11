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
        'knowledge_expert': {
            'role': 'Knowledge Expert',
            'focus': 'Scholar / Domain Expert',
            'system_prompt': 'You are a Knowledge Expert. Provide theoretical depth, academic rigor, and domain-specific knowledge.',
            'weight': 0.30
        },
        'sector_expert': {
            'role': 'Sector Expert',
            'focus': 'Industry Practitioner',
            'system_prompt': 'You are a Sector Expert. Focus on industry standards, market reality, and practical application.',
            'weight': 0.30
        },
        'regulatory_expert': {
            'role': 'Regulatory Expert',
            'focus': 'External Laws / Standards',
            'system_prompt': 'You are a Regulatory Expert. Ensure alignment with external laws, mandates, and government regulations.',
            'weight': 0.20
        },
        'compliance_expert': {
            'role': 'Compliance Expert',
            'focus': 'Internal Policy & Controls',
            'system_prompt': 'You are a Compliance Expert. Verify adherence to internal policies, risk controls, and governance.',
            'weight': 0.20
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
            'knowledge_expert': 8,
            'sector_expert': 9,
            'regulatory_expert': 10,
            'compliance_expert': 11
        }
        return axis_mapping.get(persona, 8)
