"""
TruthCore Persona Enhancement

Extends QuadPersonaEngine with multi-persona reasoning.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from backend.knowledge_algorithms.consumer import (
    execute_required_ka,
    require_output_field,
)
from backend.knowledge_algorithms.ka_master_controller import get_controller
from core.persona.quad.mathematical_framework import IntegrationFunction

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
            'weight': 0.30,
            'recursive_strategy': 'Deep recursive semantic mapping for Pillar/Branch coordinates.',
            'axis_alignment': 8,
            'constraint_set': ['Theoretical Coherence', 'Academic Citations only', 'No speculating on sector reality']
        },
        'sector_expert': {
            'role': 'Sector Expert',
            'focus': 'Industry Practitioner',
            'system_prompt': 'You are a Sector Expert. Focus on industry standards, market reality, and practical application.',
            'weight': 0.30,
            'recursive_strategy': 'Industry-specific application simulation across Sector coordinates.',
            'axis_alignment': 9,
            'constraint_set': ['Market Feasibility', 'Standard Industry Practice', 'No regulatory speculation']
        },
        'regulatory_expert': {
            'role': 'Regulatory Expert',
            'focus': 'External Laws / Standards',
            'system_prompt': 'You are a Regulatory Expert. Ensure alignment with external laws, mandates, and government regulations.',
            'weight': 0.20,
            'recursive_strategy': 'Nuremberg/Spiderweb crosswalk for multi-jurisdictional compliance.',
            'axis_alignment': 10,
            'constraint_set': ['Statutory Accuracy', 'Strict Legal Adherence', 'No internal policy blending']
        },
        'compliance_expert': {
            'role': 'Compliance Expert',
            'focus': 'Internal Policy & Controls',
            'system_prompt': 'You are a Compliance Expert. Verify adherence to internal policies, risk controls, and governance.',
            'weight': 0.20,
            'recursive_strategy': 'Internal honeycomb-octo mapping for organizational risk alignment.',
            'axis_alignment': 11,
            'constraint_set': ['Policy Compliance', 'Risk Mitigation', 'Data Privacy (Axis 13)']
        }
    }

    def __init__(self, quad_persona_engine=None):
        """Initialize with optional QuadPersonaEngine integration."""
        self.quad_persona_engine = quad_persona_engine
        self.active_personas = {}
        self.integration_function = IntegrationFunction()
        logger.info("PersonaEnhancer initialized")

    def enhance_query(self, query: str, context: dict[str, Any] = None,
                      personas: list[str] = None) -> dict[str, Any]:
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
            response = self._resolve_maybe_async(response)
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

    @staticmethod
    def _resolve_maybe_async(value: Any) -> Any:
        """Resolve coroutine values from the sync enhancement API."""
        if not hasattr(value, "__await__"):
            return value
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(value)
        if not loop.is_running():
            return asyncio.run(value)

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, value).result()

    async def _get_persona_response(self, persona_name: str, persona_config: dict[str, Any],
                                     query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Get response from a specific persona with production fallback to KA-Master."""
        if self.quad_persona_engine:
            try:
                result = await self.quad_persona_engine.process_with_persona(
                    query, persona_name, context
                )
                return {
                    'persona': persona_name,
                    'role': persona_config['role'],
                    'response': result.get('response', ''),
                    'confidence': result.get('confidence', 0.0),
                    'source': 'quad_persona_engine'
                }
            except Exception as e:
                logger.warning(f"QuadPersonaEngine failed for {persona_name}: {e}")

        # Production Fallback: Use KA-012 (Persona Simulation) via the global controller if available
        # This replaces the hardcoded placeholder strings.
        try:
            master = get_controller()
            ka_result = execute_required_ka(
                master,
                "KA-012",
                {
                    "query": query,
                    "persona_config": persona_config,
                    "context": context,
                },
            )
            persona_results = require_output_field(
                ka_result,
                "persona_results",
            )
            persona_type_by_name = {
                "knowledge_expert": "knowledge",
                "sector_expert": "sector",
                "regulatory_expert": "regulatory",
                "compliance_expert": "compliance",
            }
            expected_type = persona_type_by_name.get(persona_name, persona_name)
            selected = next(
                (
                    item
                    for item in persona_results
                    if isinstance(item, dict)
                    and item.get("persona_type") == expected_type
                ),
                None,
            )
            if selected is None:
                raise RuntimeError(
                    f"KA-012 returned no result for persona {expected_type!r}"
                )
            response = selected.get("response")
            if not isinstance(response, str) or not response:
                raise RuntimeError(
                    f"KA-012 returned no response for persona {expected_type!r}"
                )
            measured_confidence = selected.get("confidence")
            return {
                'persona': persona_name,
                'role': persona_config['role'],
                'response': response,
                'confidence': (
                    float(measured_confidence)
                    if isinstance(measured_confidence, (int, float))
                    else 0.0
                ),
                'measurement_status': selected.get(
                    "measurement_status",
                    "not_measured",
                ),
                'source': 'KA-012',
                'trace_id': ka_result.trace_id,
            }
        except Exception as exc:
            logger.error(
                "KA-012 persona execution failed for %s: %s",
                persona_name,
                exc,
            )
            return {
                'persona': persona_name,
                'role': persona_config['role'],
                'response': '',
                'confidence': 0.0,
                'measurement_status': 'failed',
                'source': 'ka_failure',
                'error': 'Persona reasoning was unavailable.',
            }

    def _synthesize_responses(self, responses: dict[str, dict[str, Any]],
                               weights: dict[str, float]) -> dict[str, Any]:
        """Synthesize multiple persona responses with quad IntegrationFunction."""
        if not responses:
            return {'content': '', 'confidence': 0}

        persona_key_map = {
            'knowledge_expert': 'knowledge',
            'sector_expert': 'sector',
            'regulatory_expert': 'regulatory',
            'compliance_expert': 'compliance',
        }
        text_outputs = {
            persona_key_map.get(name, name): str(response.get('response', ''))
            for name, response in responses.items()
            if isinstance(response, dict)
        }
        integration_context = {
            key: value
            for key, value in {
                'sector_relevance': weights.get('sector_expert'),
                'regulatory_urgency': weights.get('regulatory_expert'),
                'compliance_criticality': weights.get('compliance_expert'),
            }.items()
            if value is not None
        }
        try:
            content, dynamic_weights = self.integration_function.integrate_text(text_outputs, integration_context)
        except Exception as exc:
            logger.warning("IntegrationFunction synthesis failed; using fallback join: %s", exc)
            content = ""
            dynamic_weights = weights
        
        weighted_confidence = sum(
            responses[p].get('confidence', 0) * weights.get(p, 0.25)
            for p in responses
            if isinstance(responses[p], dict)
        )
        
        if not content:
            perspectives = [
                f"**{responses[p]['role']}**: {responses[p].get('response', '')}"
                for p in responses
                if isinstance(responses[p], dict)
            ]
            content = '\n'.join(perspectives)
        
        return {
            'content': content,
            'confidence': min(weighted_confidence, 1.0),
            'persona_count': len(responses),
            'synthesis_method': 'quad_integration_function',
            'dynamic_weights': dynamic_weights,
        }

    def get_persona_info(self, persona: str = None) -> dict[str, Any]:
        """Get information about personas."""
        if persona:
            return self.TRUTH_PERSONAS.get(persona, {})
        return self.TRUTH_PERSONAS

    def spawn_specialists(self, lane: str, count: int) -> list[dict[str, Any]]:
        """
        Spawns a pod of specialists for a specific lane.
        """
        if lane not in self.TRUTH_PERSONAS:
            return []
        
        base_config = self.TRUTH_PERSONAS[lane]
        specialists = []
        
        for i in range(count):
            spec_config = base_config.copy()
            spec_config['role'] = f"{base_config['role']} Specialist {i+1}"
            spec_config['system_prompt'] += f" You are Specialist {i+1} in the {lane} pod."
            # Adjust weight for pod members (spread evenly)
            spec_config['weight'] = base_config['weight'] / (count + 1)
            specialists.append(spec_config)
            
        return specialists

    def map_to_axis(self, persona: str) -> int:
        """Map persona to UKG axis number."""
        axis_mapping = {
            'knowledge_expert': 8,
            'sector_expert': 9,
            'regulatory_expert': 10,
            'compliance_expert': 11
        }
        return axis_mapping.get(persona, 8)


class PersonaPod:
    """
    A collection of specialists working within one of the 4 categories.
    """
    def __init__(self, lane: str, specialists: list[dict[str, Any]]):
        self.lane = lane
        self.specialists = specialists
        self.results = []

    async def execute(self, query: str, context: dict[str, Any], engine_instance: Any):
        """Executes reasoning for all specialists in the pod in parallel."""
        tasks = []
        for spec_config in self.specialists:
            tasks.append(self._run_specialist(spec_config, query, context, engine_instance))
        
        # Parallel execution with error shielding
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Specialist in pod {self.lane} failed: {res}")
            else:
                self.results.append(res)

    async def _run_specialist(self, spec_config, query, context, engine_instance):
        """Runs a single specialist analysis."""
        return await engine_instance.persona_enhancer._get_persona_response(
            spec_config['role'], spec_config, query, context
        )

    def synthesize(self) -> dict[str, Any]:
        """Synthesizes pod results into a single lane output."""
        if not self.results:
            return {}
        
        # Simple consensus synthesis for now
        combined_content = "\n".join([r.get('response', '') for r in self.results])
        avg_confidence = sum([r.get('confidence', 0) for r in self.results]) / len(self.results)
        
        return {
            'lane': self.lane,
            'content': combined_content,
            'confidence': avg_confidence,
            'specialist_count': len(self.results)
        }
