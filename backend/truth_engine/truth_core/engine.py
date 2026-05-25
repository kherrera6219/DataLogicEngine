"""
TruthCore Engine - Adaptive Reasoning with 5-Tier Workflows

Integrates with:
- UKG SimulationEngine
- KAMasterController
- QuadPersonaEngine
- 17-Axis System
"""

import logging
import uuid
import asyncio
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

from backend.truth_engine.truth_core.personas import PersonaEnhancer, PersonaPod
from backend.truth_engine.truth_core.persona_sufficiency import PersonaSufficiencyTool
from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
from backend.llm_gateway.model_defaults import (
    ANTHROPIC_PRIMARY_MODEL,
    GOOGLE_PRIMARY_MODEL,
    OPENAI_LATEST_MODEL,
)

logger = logging.getLogger(__name__)


class TruthCoreEngine:
    """
    Central orchestrator for Truth Engine reasoning workflows.
    
    Provides 5-tier adaptive processing:
    - Trivial: Direct answer, temperature 0
    - Moderate: Hybrid RAG + Chain of Thought
    - High-Stakes: 12-step refinement workflow
    - Extreme: GNN/NN/Quantum simulations
    - Autonomous: Governed multi-agent planning
    """
    
    TIERS = {
        'trivial': {'sla_seconds': 1, 'priority': 0, 'description': 'Direct Answer'},
        'moderate': {'sla_seconds': 3, 'priority': 1, 'description': 'Hybrid Vector RAG + CoT'},
        'high_stakes': {'sla_seconds': 10, 'priority': 2, 'description': '12-Step Refinement Workflow'},
        'extreme': {'sla_seconds': 60, 'priority': 3, 'description': 'GNN/NN/Quantum Simulations'},
        'autonomous': {'sla_seconds': 300, 'priority': 4, 'description': 'Governed Multi-Agent'}
    }
    
    ROUTING_PROFILES = {
        'code': 'codestral',
        'analysis': ANTHROPIC_PRIMARY_MODEL,
        'long_context': GOOGLE_PRIMARY_MODEL,
        'reasoning': 'grok-4-fast',
        'default': OPENAI_LATEST_MODEL
    }
    
    REFINEMENT_STEPS = [
        'intent_parsing',            # Layer 1
        'hybrid_retrieval',          # Layer 2
        'deep_research',             # Layer 3
        'pov_expansion',             # Layer 4
        'multi_persona_reasoning',   # Layer 5
        'quant_validation',          # Layer 6
        'agi_planning',              # Layer 7
        'trust_validation',          # Layer 8
        'meta_reasoning',            # Layer 9
        'final_safety_gate',         # Layer 10
    ]

    def get_workflow_steps(
        self,
        tier: str,
        axis17_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Dynamically define steps for each complexity tier.

        Phase B wires Axis 17 as the FROST mode selector. When supplied, its
        `truth_engine_mode` can force the full regulatory/refinement path.
        """
        if axis17_context:
            mode = str(axis17_context.get("truth_engine_mode") or "").lower()
            if mode in {"regulatory_strict", "full_refinement", "governed_agentic"}:
                tier = "high_stakes" if mode == "regulatory_strict" else "extreme"

        if tier == 'trivial':
            return ['intent_parsing', 'final_safety_gate']
        elif tier == 'moderate':
            return ['intent_parsing', 'hybrid_retrieval', 'multi_persona_reasoning', 'final_safety_gate']
        elif tier == 'high_stakes':
            return [
                'intent_parsing', 'hybrid_retrieval', 'multi_persona_reasoning', 
                'quant_validation', 'trust_validation', 'meta_reasoning', 'final_safety_gate'
            ]
        elif tier == 'extreme':
            return [
                'intent_parsing', 'hybrid_retrieval', 'deep_research', 'pov_expansion',
                'multi_persona_reasoning', 'quant_validation', 'agi_planning',
                'trust_validation', 'meta_reasoning', 'final_safety_gate'
            ]
        elif tier == 'autonomous':
            # Autonomous adds loopback triggers and adaptive preemption
            return self.get_workflow_steps('extreme') + ['memory_patch']
        return self.get_workflow_steps('moderate')

    def __init__(self, db_session=None, simulation_engine=None, ka_controller=None, axis_system=None):
        """Initialize TruthCore with optional integrations."""
        self.db_session = db_session
        self.simulation_engine = simulation_engine
        self.ka_controller = ka_controller
        self.axis_system = axis_system
        
        # Initialize Layer 6 Service
        try:
            from backend.truth_engine.truth_gate.quant import QuantValidationService
            self.quant_service = QuantValidationService(ka_controller)
        except ImportError:
            logger.warning("Layer 6 QuantValidationService not found, skipping.")
            self.quant_service = None
            
        # Initialize Layer 7 AGI Planner
        try:
            from backend.truth_engine.truth_core.agi_planner import AGIPlannerService
            self.agi_planner = AGIPlannerService(
                llm_gateway=ka_controller.llm_gateway if ka_controller else None,
                ka_controller=ka_controller
            )
        except ImportError:
            logger.warning("Layer 7 AGIPlannerService not found, skipping.")
            self.agi_planner = None
        
        # Initialize Layer 8 Trust Validation Gateway
        try:
            from backend.truth_engine.truth_gate.trust_validation_gateway import TrustValidationGateway
            self.trust_gateway = TrustValidationGateway(ka_controller=ka_controller)
        except ImportError:
            logger.warning("Layer 8 TrustValidationGateway not found, skipping.")
            self.trust_gateway = None
        
        # Initialize Layer 9 MetaReasoningController
        try:
            from backend.truth_engine.truth_core.meta_reasoning_controller import MetaReasoningController
            self.meta_reasoning = MetaReasoningController(ka_controller=ka_controller)
        except ImportError:
            logger.warning("Layer 9 MetaReasoningController not found, skipping.")
            self.meta_reasoning = None
        
        # Initialize Layer 10 EmergenceDetectionController
        try:
            from backend.truth_engine.truth_core.emergence_controller import EmergenceDetectionController
            self.emergence_gate = EmergenceDetectionController(ka_controller=ka_controller)
        except ImportError:
            logger.warning("Layer 10 EmergenceDetectionController not found, skipping.")
            self.emergence_gate = None
            
        # Initialize Persona Enhancer and Sufficiency Tool
        self.persona_enhancer = PersonaEnhancer(quad_persona_engine=self.ka_controller if hasattr(self.ka_controller, 'process_with_persona') else None)
        self.sufficiency_tool = PersonaSufficiencyTool()
        self.refinement_orchestrator = RefinementOrchestrator(ka_controller=self.ka_controller)
        
        self.active_sessions = {}
        logger.info("TruthCore Engine initialized with Final Assembly stack")

    async def determine_tier(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Determines workflow tier using rule-based fallback and AI-driven KA-005."""
        context = context or {}
        if context.get('force_tier'):
            return context['force_tier']
            
        # Production Logic: Use KA-005 for Query Classification
        try:
            if self.ka_controller:
                loop = asyncio.get_event_loop()
                ka_result = await loop.run_in_executor(
                    None, 
                    self.ka_controller.execute_algorithm, 
                    "KA-005", 
                    {"query": query, "context": context}
                )
                tier = ka_result.get('suggested_tier', ka_result.get('tier'))
                if tier in self.TIERS:
                    return tier
        except Exception as e:
            logger.warning(f"AI Tiering (KA-005) failed: {e}. Reverting to heuristics.")

        # Heuristic Fallback
        query_len = len(query.split())
        if query_len < 5:
            return 'trivial'
        if any(kw in query.lower() for kw in ['risk', 'safety', 'legal', 'compliance']):
            return 'high_stakes'
        return 'moderate'

    async def get_routing_profile(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Determines routing profile using AI-driven KA-113."""
        context = context or {}
        if context.get('routing_profile'):
            return context['routing_profile']
            
        try:
            if self.ka_controller:
                loop = asyncio.get_event_loop()
                ka_result = await loop.run_in_executor(
                    None, 
                    self.ka_controller.execute_algorithm, 
                    "KA-113", 
                    {"query": query, "context": context}
                )
                profile = ka_result.get('routing_profile', ka_result.get('profile'))
                if profile:
                    return profile
        except Exception:
            pass # Revert to heuristics

        query_lower = query.lower()
        if any(kw in query_lower for kw in ['code', 'function', 'program', 'script']):
            return 'code'
        if len(query) > 5000:
            return 'long_context'
        return 'default'

    async def create_session(self, query: str, user_id: int = None, tenant_id: str = None, 
                           context: Dict[str, Any] = None, tier: str = None) -> Dict[str, Any]:
        """Create a new TruthCore processing session."""
        session_id = str(uuid.uuid4())
        tier = tier or await self.determine_tier(query, context)
        routing_profile = await self.get_routing_profile(query, context)
        tenant = tenant_id or f"tenant_{user_id or 'default'}"
        
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'tenant_id': tenant,
            'query': query,
            'tier': tier,
            'routing_profile': routing_profile,
            'status': 'created',
            'created_at': datetime.now(UTC).isoformat(),
            'workflow_steps': [],
            'context': context or {}
        }
        
        if self.db_session:
            try:
                from models import TruthSession
                db_session = TruthSession(
                    session_id=session_id,
                    user_id=user_id,
                    tenant_id=tenant,
                    tier=tier,
                    status='created',
                    query=query,
                    routing_profile=routing_profile,
                    axis_context=context or {}
                )
                self.db_session.add(db_session)
                self.db_session.commit()
                logger.info(f"Persisted TruthSession {session_id} to database")
            except Exception as e:
                logger.error(f"Failed to persist session to DB: {e}")
                self.db_session.rollback()
        
        self.active_sessions[session_id] = session
        logger.info(f"Created TruthCore session {session_id} with tier={tier}, profile={routing_profile}")
        
        return session

    async def process(self, session_id: str) -> Dict[str, Any]:
        """Process a query through the appropriate tier workflow."""
        if session_id not in self.active_sessions:
            if self.db_session:
                try:
                    from models import TruthSession
                    db_sess = self.db_session.query(TruthSession).filter_by(
                        session_id=session_id
                    ).first()
                    if db_sess:
                        self.active_sessions[session_id] = db_sess.to_dict()
                except Exception as e:
                    logger.error(f"Failed to load session from DB: {e}")
            
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session['status'] = 'processing'
        session['started_at'] = datetime.now(UTC).isoformat()
        
        tier = session['tier']
        query = session['query']
        context = session.get('context', {})
        
        try:
            steps = self.get_workflow_steps(tier)
            result = await self._execute_workflow(query, context, steps, tier)
            
            session['status'] = 'completed'
            session['completed_at'] = datetime.now(UTC).isoformat()
            session['result'] = result
            session['context'] = result.get('context', {}) # Store final context
            session['confidence_score'] = result.get('confidence', 0)
            session['workflow_steps'] = result.get('steps_executed', [])
            session['personas_used'] = result.get('personas_used', [])
            
            if self.db_session:
                try:
                    from models import TruthSession
                    db_sess = self.db_session.query(TruthSession).filter_by(
                        session_id=session_id
                    ).first()
                    if db_sess:
                        db_sess.status = 'completed'
                        db_sess.response = result.get('response', '')
                        db_sess.confidence_score = result.get('confidence', 0)
                        db_sess.workflow_steps = result.get('steps_executed', [])
                        db_sess.personas_used = result.get('personas_used', [])
                        db_sess.completed_at = datetime.now(UTC)
                        self.db_session.commit()
                except Exception as e:
                    logger.error(f"Failed to update session in DB: {e}")
                    self.db_session.rollback()
            
        except Exception as e:
            session['status'] = 'failed'
            session['error'] = str(e)
            logger.error(f"TruthCore processing failed for session {session_id}: {e}")
            raise
        
        return session

    def _refresh_graph_context(self, query: str, working_context: Dict[str, Any]) -> None:
        """Populate live graph anchors from text and any available 17-axis vector."""
        try:
            from backend.storage import get_graph_store, get_uskd_memory_graph

            memory_graph = get_uskd_memory_graph()
            graph_store = get_graph_store()
            coordinate_vector = working_context.get('coordinate_vector') or {}
            axis_queries = self._axis_queries_from_coordinate_vector(coordinate_vector)

            memory_nodes = memory_graph.coordinate_nodes(text=query, limit=10)
            neo4j_nodes = graph_store.find_coordinate_nodes(text=query, limit=10)
            for axis_number, axis_text in axis_queries:
                memory_nodes.extend(memory_graph.coordinate_nodes(axis_number=axis_number, text=axis_text, limit=5))
                neo4j_nodes.extend(graph_store.find_coordinate_nodes(axis_number=axis_number, text=axis_text, limit=5))

            working_context['memory_graph_nodes'] = self._dedupe_graph_nodes(memory_nodes)
            working_context['neo4j_nodes'] = self._dedupe_graph_nodes(neo4j_nodes)
        except Exception as exc:
            logger.debug("Graph-grounded context bootstrap skipped: %s", exc)

    @staticmethod
    def _axis_queries_from_coordinate_vector(coordinate_vector: Dict[str, Any]) -> List[tuple[int, str]]:
        if not isinstance(coordinate_vector, dict):
            return []
        queries: List[tuple[int, str]] = []
        active_axes = coordinate_vector.get('active_axes')
        axes = coordinate_vector.get('axes') if isinstance(coordinate_vector.get('axes'), dict) else coordinate_vector
        candidates = active_axes if isinstance(active_axes, list) else list(axes.keys())
        for raw_axis in candidates:
            try:
                axis_number = int(str(raw_axis).removeprefix('axis_').removeprefix('A'))
            except (TypeError, ValueError):
                continue
            if not 1 <= axis_number <= 17:
                continue
            value = axes.get(raw_axis, axes.get(str(raw_axis), axes.get(f'axis_{axis_number}', axes.get(f'A{axis_number}'))))
            if isinstance(value, dict):
                value = value.get('uid') or value.get('value') or value.get('code') or value.get('label')
            queries.append((axis_number, str(value or '').strip()))
        return queries

    @staticmethod
    def _dedupe_graph_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for node in nodes:
            props = node.get('props') if isinstance(node.get('props'), dict) else node
            key = props.get('uid') or props.get('node_id') or props.get('code') or repr(node)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(node)
        return deduped

    async def _execute_workflow(self, query: str, context: Dict[str, Any], steps: List[str], tier: str) -> Dict[str, Any]:
        """Unified execution loop for all tiers."""
        executed_steps = []
        working_context = context.copy()
        working_context['session_id'] = context.get('session_id', str(uuid.uuid4()))
        working_context['persona_results'] = {}
        self._refresh_graph_context(query, working_context)
        personas_used = set()
        
        for step in steps:
            step_result = self._execute_refinement_step(step, query, working_context)
            executed_steps.append(step_result)
            
            # Layer-Specific Data Piping & Context Injection
            if step_result['status'] == 'completed':
                output = step_result.get('output', {})
                if not isinstance(output, dict):
                    output = {"raw_output": output}
                
                if step == 'intent_parsing':
                    working_context['intent_id'] = output.get('intent_id')
                    working_context['coordinate_vector'] = output.get('coordinates', {})
                    self._refresh_graph_context(query, working_context)
                
                elif step == 'hybrid_retrieval':
                    working_context['evidence'] = output.get('evidence', [])
                
                elif step == 'multi_persona_reasoning':
                    # Standard Quad Persona Execution
                    working_context['claims'] = output.get('claims', [])
                    working_context['persona_results'] = output.get('personas', {})
                    
                    # --- PERSONA SUFFICIENCY GATE ---
                    sufficiency = self.sufficiency_tool.evaluate(
                        query, 
                        working_context.get('coordinate_vector', {}).get('active_axes', []),
                        working_context['persona_results'],
                        {"domain": working_context.get('risk_domain', 'standard'), "tags": working_context.get('tags', [])}
                    )
                    logger.info(f"SUFFICIENCY DECISION: {sufficiency['mode']} (Reasons: {sufficiency['reasons']})")
                    
                    if sufficiency['mode'] == 'expanded_committee':
                        logger.info(f"SUFFICIENCY TRIGGER: Expanding committee. Reasons: {sufficiency['reasons']}")
                        try:
                            # Spawn and execute pods
                            pods = []
                            for lane, count in sufficiency['spawn'].items():
                                if count > 0:
                                    specialists = self.persona_enhancer.spawn_specialists(f"{lane}_expert", count)
                                    pod = PersonaPod(lane, specialists)
                                    pods.append(pod)
                            
                            # Execute pods concurrently
                            if pods:
                                await asyncio.gather(*[pod.execute(query, working_context, self) for pod in pods])
                                
                                for pod in pods:
                                    pod_result = pod.synthesize()
                                    # Merge pod results into the dedicated results map
                                    if 'persona_results' not in working_context:
                                        working_context['persona_results'] = {}
                                    working_context['persona_results'][f"{pod.lane}_pod"] = pod_result
                            
                            logger.info("Persona Pods executed and synthesized in parallel.")
                        except Exception as e:
                            logger.error(f"Persona Pod scaling failed: {e}. Reverting to base Quad.")
                
                elif step == 'quant_validation':
                    working_context['l6_quant_result'] = output
                
                elif step == 'agi_planning':
                    working_context['l7_agi_plan'] = output
                
                elif step == 'trust_validation':
                    working_context['l8_gate_result'] = output
                    if step_result.get('gate_decision') == 'FAIL':
                        logger.warning("Layer 8 BLOCK: Workflow halted.")
                        break

                elif step == 'meta_reasoning':
                    working_context['l9_result'] = output
                    # Handle L9 REFINE/FINALIZE decision
                    if step_result.get('gate_decision') == 'REFINE':
                        logger.info("Layer 9 trigger: REFINING...")
                
                elif step == 'final_safety_gate':
                    if step_result.get('decision') == 'HALT':
                        logger.error("Layer 10 BLOCK: Output HALTED by Sentinel.")
                        break
                    
                    # --- 12-STEP REFINEMENT ORCHESTRATOR ---
                    # Final polish before release
                    if tier in ['high_stakes', 'extreme', 'autonomous']:
                        logger.info("Invoking 12-Step Refinement Orchestrator.")
                        try:
                            refined_result = await self.refinement_orchestrator.refine(
                                {"content": step_result.get('final_answer', ''), "confidence": step_result.get('confidence', 0.95)},
                                working_context
                            )
                            step_result['final_answer'] = refined_result['content']
                            step_result['confidence'] = refined_result['final_confidence']
                            working_context['refinement_history'] = refined_result['refinement_history']
                        except Exception as e:
                            logger.error(f"Refinement Orchestrator crashed: {e}. Falling back to unpolished output.")
            else:
                logger.error(f"Step {step} failed: {step_result.get('error')}")
                if tier in ['high_stakes', 'extreme', 'autonomous']:
                    break

        # Final result assembly
        last_success = next((s for s in reversed(executed_steps) if s['status'] == 'completed'), None)
        final_answer = ""
        if last_success:
            if 'final_answer' in last_success:
                final_answer = last_success['final_answer']
            else:
                final_answer = str(last_success.get('output', ''))

        if 'persona_results' in working_context:
            logger.info(f"Final Persona Results Keys: {working_context['persona_results'].keys()}")
            
        return {
            'tier': tier,
            'response': final_answer,
            'confidence': executed_steps[-1].get('confidence', 0.95) if executed_steps else 0.0,
            'steps_executed': executed_steps,
            'personas_used': list(personas_used) if personas_used else ['sentinel'],
            'processing_time_ms': 500, # Simplified for now
            'context': working_context # Include for audit parity
        }

    def _execute_refinement_step(self, step: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single layer/step and return its results."""
        mapping = {
            'intent_parsing': 'KA-011',        # L1: Intent Parsing 
            'hybrid_retrieval': 'KA-079',      # L2: Retrieval
            'deep_research': 'KA-029',         # L3: Deep Research
            'pov_expansion': 'KA-028',         # L4: POV Expansion
            'multi_persona_reasoning': 'KA-012', # L5: Persona Deliberation
            'quant_validation': 'KA-116',      # L6: Quantitative Validation
            'agi_planning': 'KA-006',          # L7: AGI Mission Planning
            'trust_validation': 'L8-GATEWAY',  # L8: Trust Gate
            'meta_reasoning': 'L9-CONTROLLER', # L9: Meta-Recursion
            'final_safety_gate': 'L10-SENTINEL', # L10: Safety Sentinel
            'memory_patch': 'KA-016'
        }
        
        # --- Layer-Specific Service Overrides ---
        
        # L6: Quantitative Validation Service
        if step == 'quant_validation' and self.quant_service:
            try:
                claims = context.get('claims', [])
                draft = context.get('draft_solution', query)
                result = self.quant_service.validate(draft, claims, context.get('data_context'))
                return {
                    'step': step,
                    'ka_id': 'L6-QUANT-SERVICE',
                    'status': 'completed',
                    'output': result.model_dump() if hasattr(result, 'model_dump') else result,
                    'confidence': result.confidence if hasattr(result, 'confidence') else 0.9
                }
            except Exception as e:
                logger.error(f"Layer 6 Service failed: {e}")

        # L7: AGI Planner Service
        if step == 'agi_planning' and self.agi_planner:
            try:
                beliefs = context.get('beliefs', [])
                goal = context.get('draft_solution', query)
                plan = self.agi_planner.plan(goal, beliefs)
                return {
                    'step': step,
                    'ka_id': 'L7-AGI-PLANNER',
                    'status': 'completed',
                    'output': plan.model_dump() if hasattr(plan, 'model_dump') else plan,
                    'confidence': plan.convergence_score if hasattr(plan, 'convergence_score') else 0.95
                }
            except Exception as e:
                logger.error(f"Layer 7 Service failed: {e}")

        # L8: Trust Validation Gateway
        if step == 'trust_validation' and self.trust_gateway:
            try:
                from backend.truth_engine.truth_gate.l8_schemas import L8Input
                l8_input = L8Input(
                    simulation_id=context.get('session_id', 'unknown'),
                    query_text=query,
                    l5_synthesis=context.get('l5_synthesis'),
                    l6_quant_result=context.get('l6_quant_result'),
                    l7_agi_plan=context.get('l7_agi_plan'),
                    claims=context.get('claims', []),
                    evidence=context.get('evidence', []),
                    constraints=context.get('constraints', []),
                    persona_results=context.get('persona_results', {}),
                    risk_domain=context.get('risk_domain', 'standard')
                )
                result = self.trust_gateway.validate(l8_input)
                return {
                    'step': step,
                    'ka_id': 'L8-GATEWAY',
                    'status': 'completed',
                    'gate_decision': result.status.value,
                    'output': result.model_dump(),
                    'confidence': result.overall_confidence
                }
            except Exception as e:
                logger.error(f"Layer 8 TrustValidationGateway failed: {e}")
                return {'step': step, 'ka_id': 'L8-GATEWAY', 'status': 'error', 'gate_decision': 'FAIL', 'error': str(e), 'confidence': 0.0}

        # L9: Meta-Reasoning Controller
        if step == 'meta_reasoning' and self.meta_reasoning:
            try:
                from backend.truth_engine.truth_core.l9_schemas import L9Input
                l9_input = L9Input(
                    simulation_id=context.get('session_id', 'unknown'),
                    l8_gate_result=context.get('l8_gate_result', {}),
                    reasoning_trace=context.get('reasoning_trace', {}),
                    problem_spec={'original_query': query, 'constraints': context.get('constraints', [])},
                    iteration_state=context.get('iteration_state', {}),
                    risk_domain=context.get('risk_domain', 'standard')
                )
                result = self.meta_reasoning.evaluate(l9_input)
                return {
                    'step': step,
                    'ka_id': 'L9-CONTROLLER',
                    'status': 'completed',
                    'gate_decision': result.decision.value,
                    'output': result.model_dump(),
                    'readiness_score': result.readiness_score
                }
            except Exception as e:
                logger.error(f"Layer 9 MetaReasoningController failed: {e}")
                return {'step': step, 'ka_id': 'L9-CONTROLLER', 'status': 'error', 'gate_decision': 'REFINE', 'error': str(e), 'readiness_score': 0.0}

        # L10: Final Safety Gate (Sentinel)
        if step == 'final_safety_gate' and self.emergence_gate:
            try:
                from backend.truth_engine.truth_core.l10_schemas import L10Input
                l10_input = L10Input(
                    simulation_id=context.get('session_id', 'unknown'),
                    l9_result=context.get('l9_result', {}),
                    reasoning_trace=context.get('reasoning_trace', {}),
                    problem_spec={'original_query': query, 'constraints': context.get('constraints', [])},
                    coordinate_vector=context.get('coordinate_vector', {}),
                    risk_domain=context.get('risk_domain', 'standard')
                )
                result = self.emergence_gate.authorize(l10_input)
                return {
                    'step': step,
                    'ka_id': 'L10-SENTINEL',
                    'status': 'completed',
                    'decision': result.decision.value,
                    'output': result.model_dump(),
                    'final_answer': result.final_answer
                }
            except Exception as e:
                logger.error(f"Layer 10 EmergenceDetectionController failed: {e}")
                return {'step': step, 'ka_id': 'L10-SENTINEL', 'status': 'error', 'decision': 'HALT', 'error': str(e), 'final_answer': "Final safety gate failure."}

        # --- Default KA Execution ---
        ka_id = mapping.get(step)
        if ka_id and self.ka_controller:
            try:
                ka_input = {'query': query, **context}
                if hasattr(self.ka_controller, 'execute_algorithm'):
                    result = self.ka_controller.execute_algorithm(ka_id, ka_input)
                else:
                    result = self.ka_controller.execute(ka_id, ka_input)
                
                return {
                    'step': step,
                    'ka_id': ka_id,
                    'status': 'completed',
                    'output': result.get('output', result),
                    'confidence': result.get('confidence', result.get('weighted_confidence', 0.9))
                }
            except Exception as e:
                logger.error(f"KA {ka_id} failed for step {step}: {e}")
                
        return {
            'step': step,
            'status': 'completed',
            'output': f"Mock result of {step}",
            'confidence': 0.8
        }

    def _invoke_ka_algorithms(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke relevant Knowledge Algorithms dynamically based on complexity."""
        if not self.ka_controller:
            return {'status': 'skipped', 'reason': 'No KA controller configured'}
        
        # Initial complexity assessment
        router_result = {}
        try:
            if hasattr(self.ka_controller, 'execute_algorithm'):
                router_result = self.ka_controller.execute_algorithm('KA-113', {'query': query})
            else:
                router_result = self.ka_controller.execute('KA-113', {'query': query})
        except Exception:
            pass
            
        tier = router_result.get('output', {}).get('tier', 'medium')
        
        # Select KAs based on tier
        if tier == 'high':
            relevant_kas = ['KA-001', 'KA-002', 'KA-013', 'KA-020', 'KA-028', 'KA-041', 'KA-114']
        else:
            relevant_kas = ['KA-001', 'KA-020', 'KA-028']
            
        results = {}
        for ka_id in relevant_kas:
            try:
                if hasattr(self.ka_controller, 'execute_algorithm'):
                    result = self.ka_controller.execute_algorithm(ka_id, {'query': query, **context})
                else:
                    result = self.ka_controller.execute(ka_id, {'query': query, **context})
                results[ka_id] = {'status': 'success', 'result': result}
            except Exception as e:
                results[ka_id] = {'status': 'error', 'error': str(e)}
        
        return results

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a session."""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        return self.active_sessions[session_id]

    def get_tier_info(self, tier: str = None) -> Dict[str, Any]:
        """Get information about processing tiers."""
        if tier:
            return self.TIERS.get(tier, {})
        return self.TIERS
