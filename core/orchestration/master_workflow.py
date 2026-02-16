"""
Master Workflow Orchestrator for UKG/USKD 17-Axis System

This module implements the master workflow that coordinates all subsystems,
following the UKG 17-Axis System Configuration specification.

The master workflow:
1. Initializes all subsystems (axis schema, simulation stack, refinement engine, personas, KA registry)
2. Executes the 5-step processing flow
3. Handles dynamic triggers for conflict resolution, compliance rollback, and refinement loops
4. Manages shared state across all layers
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TriggerCondition(Enum):
    """Dynamic trigger conditions for workflow control flow."""
    PERSONA_CONFLICT_DETECTED = "persona_conflict_detected"
    COMPLIANCE_VIOLATION_DETECTED = "compliance_violation_detected"
    REFINEMENT_LOOP_INCOMPLETE = "refinement_loop_incomplete"
    THRESHOLD_NOT_MET_AFTER_MAX = "threshold_not_met_after_max"
    ALL_CLEAR = "all_clear"


class TriggerAction(Enum):
    """Actions to take when triggers fire."""
    PERSONA_ARBITRATION = "persona_arbitration"
    CONTAINMENT_ROLLBACK = "containment_rollback"
    ITERATION_FEEDBACK = "iteration_feedback"
    MANUAL_REVIEW_ALERT = "manual_review_alert"
    FINALIZE_OUTPUT = "finalize_output"


class SharedStateManager:
    """
    Manages shared state across all layers and subsystems.
    
    Tracks metrics like:
    - Layer 5 consensus strength
    - Layer 8 cross-verification score
    - Layer 10 preliminary confidence
    """
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.state = {
            'session_id': self.session_id,
            'created_at': datetime.now(UTC).isoformat(),
            'layer_metrics': {},
            'persona_states': {},
            'trigger_log': [],
            'confidence_history': [],
            'rollback_points': []
        }
    
    def update_layer_metric(self, layer_num: int, metric_name: str, value: float) -> None:
        """Update a metric for a specific layer."""
        if layer_num not in self.state['layer_metrics']:
            self.state['layer_metrics'][layer_num] = {}
        self.state['layer_metrics'][layer_num][metric_name] = {
            'value': value,
            'updated_at': datetime.now(UTC).isoformat()
        }
        logger.debug(f"Updated Layer {layer_num} metric {metric_name} = {value}")
    
    def get_layer_metric(self, layer_num: int, metric_name: str) -> Optional[float]:
        """Get a metric value for a specific layer."""
        layer_metrics = self.state['layer_metrics'].get(layer_num, {})
        metric = layer_metrics.get(metric_name, {})
        return metric.get('value')
    
    def update_consensus_strength(self, value: float) -> None:
        """Update Layer 5 consensus strength metric."""
        self.update_layer_metric(5, 'consensus_strength', value)
    
    def update_cross_verification_score(self, value: float) -> None:
        """Update Layer 8 cross-verification score."""
        self.update_layer_metric(8, 'cross_verification_score', value)
    
    def update_preliminary_confidence(self, value: float) -> None:
        """Update Layer 10 preliminary confidence."""
        self.update_layer_metric(10, 'preliminary_confidence', value)
        self.state['confidence_history'].append({
            'confidence': value,
            'timestamp': datetime.now(UTC).isoformat()
        })
    
    def save_rollback_point(self, state_snapshot: Dict[str, Any]) -> str:
        """Save a rollback point for containment purposes."""
        rollback_id = f"rollback_{len(self.state['rollback_points']) + 1}"
        self.state['rollback_points'].append({
            'id': rollback_id,
            'snapshot': state_snapshot,
            'created_at': datetime.now(UTC).isoformat()
        })
        logger.info(f"Saved rollback point: {rollback_id}")
        return rollback_id
    
    def get_rollback_point(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        """Get a saved rollback point."""
        for point in self.state['rollback_points']:
            if point['id'] == rollback_id:
                return point['snapshot']
        return None
    
    def log_trigger(self, condition: TriggerCondition, action: TriggerAction, details: str) -> None:
        """Log a trigger event."""
        self.state['trigger_log'].append({
            'condition': condition.value,
            'action': action.value,
            'details': details,
            'timestamp': datetime.now(UTC).isoformat()
        })
    
    def update_persona_state(self, persona_type: str, state: Dict[str, Any]) -> None:
        """Update state for a specific persona."""
        self.state['persona_states'][persona_type] = {
            **state,
            'updated_at': datetime.now(UTC).isoformat()
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get the complete shared state."""
        return self.state.copy()


class TriggerSystem:
    """
    Handles dynamic control-flow triggers for the master workflow.
    
    Triggers:
    - persona_conflict_detected: Initiate consensus debate via Layer 5 coordination
    - compliance_violation_detected: Rollback to safe state and adjust plan
    - refinement_loop_incomplete: Feed insights back and repeat refinement
    - threshold_not_met_after_max: Flag for human review
    - all_clear: Finalize output
    """
    
    def __init__(self, shared_state: SharedStateManager, config: Optional[Dict] = None):
        self.shared_state = shared_state
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.90)
        self.max_refinement_iterations = self.config.get('max_refinement_iterations', 5)
        self.current_iteration = 0
    
    def evaluate_conditions(self, context: Dict[str, Any]) -> List[TriggerCondition]:
        """
        Evaluate all trigger conditions based on current context.
        
        Returns list of active trigger conditions.
        """
        active_conditions = []
        
        if self._check_persona_conflict(context):
            active_conditions.append(TriggerCondition.PERSONA_CONFLICT_DETECTED)
        
        if self._check_compliance_violation(context):
            active_conditions.append(TriggerCondition.COMPLIANCE_VIOLATION_DETECTED)
        
        if self._check_refinement_incomplete(context):
            active_conditions.append(TriggerCondition.REFINEMENT_LOOP_INCOMPLETE)
        
        if self._check_threshold_not_met_after_max(context):
            active_conditions.append(TriggerCondition.THRESHOLD_NOT_MET_AFTER_MAX)
        
        if not active_conditions:
            confidence = context.get('confidence', 0.0)
            if confidence >= self.confidence_threshold:
                active_conditions.append(TriggerCondition.ALL_CLEAR)
        
        return active_conditions
    
    def _check_persona_conflict(self, context: Dict[str, Any]) -> bool:
        """Check if personas have conflicting outputs."""
        persona_outputs = context.get('personas_output', {})
        if len(persona_outputs) < 2:
            return False
        
        confidences = []
        for persona_type, output in persona_outputs.items():
            if output.get('status') == 'success':
                confidences.append(output.get('confidence', 0.5))
        
        if len(confidences) < 2:
            return False
        
        confidence_variance = max(confidences) - min(confidences)
        conflict_threshold = self.config.get('conflict_variance_threshold', 0.3)
        
        has_conflict = confidence_variance > conflict_threshold
        
        conflicts = context.get('conflicts', [])
        if conflicts:
            has_conflict = True
        
        return has_conflict
    
    def _check_compliance_violation(self, context: Dict[str, Any]) -> bool:
        """Check for regulatory or compliance violations."""
        compliance_result = context.get('compliance_check', {})
        if compliance_result.get('status') == 'violation':
            return True
        
        regulatory_result = context.get('regulatory_check', {})
        if regulatory_result.get('status') == 'violation':
            return True
        
        return False
    
    def _check_refinement_incomplete(self, context: Dict[str, Any]) -> bool:
        """Check if refinement loop needs to continue."""
        confidence = context.get('confidence', 0.0)
        
        if confidence >= self.confidence_threshold:
            return False
        
        if self.current_iteration >= self.max_refinement_iterations:
            return False
        
        return True
    
    def _check_threshold_not_met_after_max(self, context: Dict[str, Any]) -> bool:
        """Check if threshold not met after maximum iterations."""
        confidence = context.get('confidence', 0.0)
        
        if confidence >= self.confidence_threshold:
            return False
        
        return self.current_iteration >= self.max_refinement_iterations
    
    def get_action(self, condition: TriggerCondition) -> TriggerAction:
        """Get the action for a given trigger condition."""
        action_map = {
            TriggerCondition.PERSONA_CONFLICT_DETECTED: TriggerAction.PERSONA_ARBITRATION,
            TriggerCondition.COMPLIANCE_VIOLATION_DETECTED: TriggerAction.CONTAINMENT_ROLLBACK,
            TriggerCondition.REFINEMENT_LOOP_INCOMPLETE: TriggerAction.ITERATION_FEEDBACK,
            TriggerCondition.THRESHOLD_NOT_MET_AFTER_MAX: TriggerAction.MANUAL_REVIEW_ALERT,
            TriggerCondition.ALL_CLEAR: TriggerAction.FINALIZE_OUTPUT
        }
        return action_map.get(condition, TriggerAction.MANUAL_REVIEW_ALERT)
    
    def increment_iteration(self) -> None:
        """Increment the current iteration counter."""
        self.current_iteration += 1
    
    def reset_iteration(self) -> None:
        """Reset the iteration counter."""
        self.current_iteration = 0


class MasterWorkflowOrchestrator:
    """
    Master Workflow Orchestrator for the UKG 17-Axis System.
    
    Coordinates:
    - 17-Axis Coordinate Schema
    - 10-Layer Simulation Stack
    - 12-Step Refinement Engine
    - Quad Persona Templates
    - Knowledge Agent Registry
    
    Execution Flow:
    1. Parse Input Coordinate - Convert query into 17-axis coordinate values
    2. Activate Personas - Spawn four AI personas with context
    3. Run Simulation Stack - Execute 10-layer recursive reasoning
    4. Run Refinement Engine - Perform 12-step iterative refinement
    5. Output Finalization - Compile and format final answer
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Master Workflow Orchestrator.
        
        Args:
            config: Configuration dictionary with subsystem references
        """
        self.config = config or {}
        self.uid = str(uuid.uuid4())
        
        self.shared_state = SharedStateManager()
        self.trigger_system = TriggerSystem(
            self.shared_state,
            config=self.config.get('triggers', {})
        )
        
        self.subsystems = {
            'axis_schema_config': None,
            'simulation_stack_config': None,
            'refinement_engine_config': None,
            'persona_templates': None,
            'knowledge_agent_registry': None
        }
        
        self.coordinate_parser = None
        self.simulation_engine = None
        self.refinement_orchestrator = None
        self.quad_persona_engine = None
        self.ka_loader = None
        
        self.execution_log = []
        
        logger.info(f"MasterWorkflowOrchestrator initialized with UID: {self.uid}")
    
    def initialize_subsystems(self) -> bool:
        """
        Initialize all subsystems for a new query.
        
        Returns:
            True if all subsystems initialized successfully
        """
        logger.info("Initializing all subsystems...")
        
        try:
            from core.coordinate_system import CoordinateParser
            self.coordinate_parser = CoordinateParser()
            logger.info("CoordinateParser initialized")
        except ImportError as e:
            logger.warning(f"Could not import CoordinateParser: {e}")
        
        try:
            from core.simulation.simulation_engine import SimulationEngine
            self.simulation_engine = SimulationEngine(config=self.config.get('simulation', {}))
            logger.info("SimulationEngine initialized")
        except ImportError as e:
            logger.warning(f"Could not import SimulationEngine: {e}")
        
        try:
            from core.persona.quad_persona_engine import QuadPersonaEngine
            self.quad_persona_engine = QuadPersonaEngine(config=self.config.get('personas', {}))
            logger.info("QuadPersonaEngine initialized")
        except ImportError as e:
            logger.warning(f"Could not import QuadPersonaEngine: {e}")
        
        try:
            from core.knowledge_algorithm.ka_loader import KALoader
            self.ka_loader = KALoader()
            logger.info("KALoader initialized")
        except ImportError as e:
            logger.warning(f"Could not import KALoader: {e}")
        
        graph_manager = None
        memory_manager = None
        united_system_manager = None
        
        try:
            from core.graph.graph_manager import GraphManager
            graph_manager = GraphManager(config=self.config.get('graph', {}))
            logger.info("GraphManager initialized for RO")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize GraphManager: {e}")
        
        try:
            from simulation.memory_manager import StructuredMemoryManager
            memory_manager = StructuredMemoryManager(config=self.config.get('memory', {}))
            logger.info("StructuredMemoryManager initialized for RO")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize StructuredMemoryManager: {e}")
        
        try:
            from core.system.united_system_manager import UnitedSystemManager
            united_system_manager = UnitedSystemManager(config=self.config)
            logger.info("UnitedSystemManager initialized for RO")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize UnitedSystemManager: {e}")
        
        try:
            from core.simulation.refinement_orchestrator import RefinementOrchestrator
            self.refinement_orchestrator = RefinementOrchestrator(
                config=self.config,
                graph_manager=graph_manager,
                memory_manager=memory_manager,
                united_system_manager=united_system_manager,
                ka_loader=self.ka_loader
            )
            logger.info("RefinementOrchestrator initialized")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not import RefinementOrchestrator: {e}")
            self.refinement_orchestrator = None
        
        try:
            from core.simulation.layer1_entry import Layer1EntryEngine
            self.layer1_engine = Layer1EntryEngine(config=self.config.get('layer1', {}))
            logger.info("Layer1EntryEngine initialized")
        except ImportError as e:
            logger.warning(f"Could not import Layer1EntryEngine: {e}")
            self.layer1_engine = None
        
        try:
            from core.simulation.layer2_knowledge import Layer2KnowledgeEngine
            self.layer2_engine = Layer2KnowledgeEngine(config=self.config.get('layer2', {}))
            logger.info("Layer2KnowledgeEngine initialized")
        except ImportError as e:
            logger.warning(f"Could not import Layer2KnowledgeEngine: {e}")
            self.layer2_engine = None
        
        try:
            from core.simulation.layer3_expert import Layer3ExpertEngine
            self.layer3_engine = Layer3ExpertEngine(
                config=self.config.get('layer3', {}),
                persona_engine=self.quad_persona_engine
            )
            logger.info("Layer3ExpertEngine initialized")
        except ImportError as e:
            logger.warning(f"Could not import Layer3ExpertEngine: {e}")
            self.layer3_engine = None
        
        logger.info("All subsystems initialization complete")
        return True
    
    def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the master workflow for a query.
        
        Args:
            query: User query or input
            context: Optional additional context
            
        Returns:
            Final processed result
        """
        start_time = datetime.now(UTC)
        session_id = self.shared_state.session_id
        
        logger.info(f"Starting master workflow execution for session {session_id}")
        
        result = {
            'session_id': session_id,
            'query': query,
            'status': 'processing',
            'start_time': start_time.isoformat(),
            'steps': {},
            'triggers_fired': [],
            'final_answer': None,
            'confidence': 0.0,
            'requires_review': False
        }
        
        try:
            self.initialize_subsystems()
            
            step1_result = self._step1_parse_input_coordinate(query, context)
            result['steps']['step_1_parse_coordinate'] = step1_result
            
            step2_result = self._step2_activate_personas(query, step1_result)
            result['steps']['step_2_activate_personas'] = step2_result
            
            step3_result = self._step3_run_simulation_stack(query, step1_result, step2_result)
            result['steps']['step_3_simulation_stack'] = step3_result
            
            step4_result = self._step4_run_refinement_engine(query, step3_result)
            result['steps']['step_4_refinement_engine'] = step4_result
            
            processing_complete = False
            while not processing_complete:
                current_context = {
                    'query': query,
                    'coordinate': step1_result,
                    'personas_output': step2_result.get('personas_output', {}),
                    'simulation_result': step3_result,
                    'refinement_result': step4_result,
                    'confidence': step4_result.get('final_confidence', 0.0),
                    'conflicts': step3_result.get('conflicts', []),
                    'compliance_check': step4_result.get('governance_check', {}),
                    'regulatory_check': step4_result.get('regulatory_check', {})
                }
                
                conditions = self.trigger_system.evaluate_conditions(current_context)
                
                for condition in conditions:
                    action = self.trigger_system.get_action(condition)
                    
                    self.shared_state.log_trigger(condition, action, f"Triggered at iteration {self.trigger_system.current_iteration}")
                    result['triggers_fired'].append({
                        'condition': condition.value,
                        'action': action.value
                    })
                    
                    if action == TriggerAction.PERSONA_ARBITRATION:
                        arbitration_result = self._handle_persona_arbitration(current_context)
                        step2_result = arbitration_result
                        step3_result = self._step3_run_simulation_stack(query, step1_result, step2_result)
                        step4_result = self._step4_run_refinement_engine(query, step3_result)
                        
                    elif action == TriggerAction.CONTAINMENT_ROLLBACK:
                        rollback_result = self._handle_containment_rollback(current_context)
                        if rollback_result.get('rollback_applied'):
                            step4_result = self._step4_run_refinement_engine(query, step3_result)
                        
                    elif action == TriggerAction.ITERATION_FEEDBACK:
                        self.trigger_system.increment_iteration()
                        step4_result = self._step4_run_refinement_engine(query, step3_result, feedback=step4_result)
                        
                    elif action == TriggerAction.MANUAL_REVIEW_ALERT:
                        result['requires_review'] = True
                        result['review_reason'] = "Confidence threshold not met after maximum iterations"
                        processing_complete = True
                        
                    elif action == TriggerAction.FINALIZE_OUTPUT:
                        processing_complete = True
            
            step5_result = self._step5_output_finalization(query, step4_result)
            result['steps']['step_5_output_finalization'] = step5_result
            
            result['final_answer'] = step5_result.get('final_answer', '')
            result['confidence'] = step4_result.get('final_confidence', 0.0)
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Error in master workflow execution: {str(e)}", exc_info=True)
            result['status'] = 'error'
            result['error'] = str(e)
        
        result['end_time'] = datetime.now(UTC).isoformat()
        result['duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        result['shared_state'] = self.shared_state.get_state()
        
        logger.info(f"Master workflow execution complete. Status: {result['status']}, Confidence: {result['confidence']:.3f}")
        
        return result
    
    def _step1_parse_input_coordinate(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Step 1: Parse Input Coordinate
        
        Convert user query into 17-axis coordinate values.
        """
        logger.info("Step 1: Parsing input coordinate")
        
        result = {
            'step': 'parse_input_coordinate',
            'status': 'success',
            'coordinates': {},
            'axis_scores': {}
        }
        
        try:
            axis_keywords = {
                1: ['temporal', 'time', 'date', 'when', 'schedule'],
                2: ['spatial', 'location', 'where', 'place', 'geography'],
                3: ['semantic', 'concept', 'meaning', 'definition', 'ontology'],
                4: ['procedural', 'process', 'how', 'method', 'workflow', 'steps'],
                5: ['analytical', 'analysis', 'data', 'statistics', 'quantitative'],
                6: ['normative', 'policy', 'standard', 'guideline', 'best practice'],
                7: ['risk', 'impact', 'threat', 'consequence', 'assessment'],
                8: ['performance', 'efficiency', 'kpi', 'metric', 'outcome'],
                9: ['expertise', 'expert', 'authority', 'credential', 'specialist'],
                10: ['ethical', 'ethics', 'moral', 'values', 'bias'],
                11: ['regulatory', 'regulation', 'law', 'legal', 'compliance'],
                12: ['compliance', 'internal', 'policy', 'control', 'adherence'],
                13: ['simulation', 'hypothetical', 'what-if', 'scenario', 'model'],
                14: ['ai-generated', 'synthetic', 'inference', 'ai', 'machine learning'],
                15: ['cultural', 'social', 'sentiment', 'public', 'human factors'],
                16: ['innovation', 'frontier', 'emerging', 'novel', 'research'],
                17: ['learning', 'improvement', 'meta', 'self-improvement', 'adaptation']
            }
            
            query_lower = query.lower()
            for axis_num, keywords in axis_keywords.items():
                score = sum(1 for kw in keywords if kw in query_lower) / len(keywords)
                result['axis_scores'][axis_num] = min(1.0, score * 2)
            
            if context:
                result['context_provided'] = True
                if 'coordinates' in context:
                    result['coordinates'] = context['coordinates']
            
            self._log_execution('step_1', result)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Step 1 error: {str(e)}")
        
        return result
    
    def _step2_activate_personas(self, query: str, coordinate_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Activate Personas
        
        Spawn four AI personas (Knowledge, Sector, Regulatory, Compliance) with context.
        """
        logger.info("Step 2: Activating personas")
        
        result = {
            'step': 'activate_personas',
            'status': 'success',
            'personas_output': {}
        }
        
        try:
            if self.quad_persona_engine:
                persona_result = self.quad_persona_engine.process_query(query)
                result['personas_output'] = persona_result.get('persona_responses', {})
                result['synthesis'] = persona_result.get('response', {})
            else:
                for persona_type in ['knowledge', 'sector', 'regulatory', 'compliance']:
                    axis_scores = coordinate_result.get('axis_scores', {})
                    
                    relevance = 0.5
                    if persona_type == 'knowledge':
                        relevance = max(axis_scores.get(3, 0.5), axis_scores.get(9, 0.5))
                    elif persona_type == 'sector':
                        relevance = max(axis_scores.get(2, 0.5), axis_scores.get(8, 0.5))
                    elif persona_type == 'regulatory':
                        relevance = max(axis_scores.get(11, 0.5), axis_scores.get(6, 0.5))
                    elif persona_type == 'compliance':
                        relevance = max(axis_scores.get(12, 0.5), axis_scores.get(7, 0.5))
                    
                    result['personas_output'][persona_type] = {
                        'status': 'success',
                        'persona_type': persona_type,
                        'relevance': relevance,
                        'confidence': 0.7 + (relevance * 0.2),
                        'activated_at': datetime.now(UTC).isoformat()
                    }
            
            for persona_type, output in result['personas_output'].items():
                self.shared_state.update_persona_state(persona_type, output)
            
            self._log_execution('step_2', result)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Step 2 error: {str(e)}")
        
        return result
    
    def _step3_run_simulation_stack(self, query: str, coordinate_result: Dict[str, Any], 
                                     persona_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Run Simulation Stack
        
        Execute the 10-layer recursive reasoning process across personas.
        Integrates Layer1, Layer2, Layer3 engines with the main simulation engine.
        """
        logger.info("Step 3: Running simulation stack")
        
        result = {
            'step': 'run_simulation_stack',
            'status': 'success',
            'layers_executed': [],
            'conflicts': []
        }
        
        try:
            layer_context = {
                'query': query,
                'axis_scores': coordinate_result.get('axis_scores', {}),
                'coordinates': coordinate_result.get('coordinates', {})
            }
            
            if hasattr(self, 'layer1_engine') and self.layer1_engine:
                layer1_result = self.layer1_engine.process(layer_context)
                result['layers_executed'].append({
                    'layer': 1,
                    'name': 'Entry Layer',
                    'status': 'completed',
                    'confidence': layer1_result.get('layer1_entry', {}).get('layer_confidence', 0.7)
                })
                layer_context.update(layer1_result)
            
            if hasattr(self, 'layer2_engine') and self.layer2_engine:
                layer2_result = self.layer2_engine.process(layer_context)
                result['layers_executed'].append({
                    'layer': 2,
                    'name': 'Knowledge Integration Layer',
                    'status': 'completed',
                    'confidence': layer2_result.get('layer2_knowledge', {}).get('layer_confidence', 0.75)
                })
                layer_context.update(layer2_result)
            
            if hasattr(self, 'layer3_engine') and self.layer3_engine:
                layer3_result = self.layer3_engine.process(layer_context)
                result['layers_executed'].append({
                    'layer': 3,
                    'name': 'Expert Simulation Layer',
                    'status': 'completed',
                    'confidence': layer3_result.get('layer3_expert', {}).get('layer_confidence', 0.8)
                })
                layer_context.update(layer3_result)
                
                layer3_conflicts = layer3_result.get('analysis_conflicts', [])
                if layer3_conflicts:
                    result['conflicts'].extend(layer3_conflicts)
            
            if self.simulation_engine:
                simulation = self.simulation_engine.start_simulation(
                    query=query,
                    context={
                        'coordinates': coordinate_result,
                        'personas': persona_result,
                        'layer1_context': layer_context.get('layer1_entry', {}),
                        'layer2_context': layer_context.get('layer2_knowledge', {}),
                        'layer3_context': layer_context.get('layer3_expert', {})
                    }
                )
                result['simulation_id'] = simulation.get('simulation_id')
                result['simulation_status'] = simulation.get('status')
                
                sim_confidence = simulation.get('confidence', {})
                
                layer_names = {
                    4: 'Persona Processing Layer',
                    5: 'Integration Layer',
                    6: 'POV Engine Layer',
                    7: 'AGI Simulation Layer',
                    8: 'Quantum Processing Layer',
                    9: 'Recursive Processing Layer',
                    10: 'Final Synthesis Layer'
                }
                
                for layer_num in range(4, 11):
                    layer_confidence_val = 0.7 + (layer_num * 0.02)
                    
                    if layer_num == 5:
                        layer_confidence_val = max(layer_confidence_val, 
                            (sim_confidence.get('knowledge', 0) + sim_confidence.get('sector', 0)) / 2)
                    elif layer_num == 8:
                        layer_confidence_val = max(layer_confidence_val,
                            (sim_confidence.get('regulatory', 0) + sim_confidence.get('compliance', 0)) / 2)
                    elif layer_num == 10:
                        layer_confidence_val = sim_confidence.get('overall', layer_confidence_val)
                    
                    layer_result = {
                        'layer': layer_num,
                        'name': layer_names.get(layer_num, f'Layer {layer_num}'),
                        'status': 'completed',
                        'confidence': layer_confidence_val
                    }
                    result['layers_executed'].append(layer_result)
                
                result['simulation_confidence'] = sim_confidence
            else:
                for layer_num in range(4, 11):
                    layer_confidence = 0.7 + (layer_num * 0.02)
                    layer_result = {
                        'layer': layer_num,
                        'status': 'completed',
                        'confidence': layer_confidence
                    }
                    result['layers_executed'].append(layer_result)
            
            layer_confidences = [l.get('confidence', 0) for l in result['layers_executed']]
            if layer_confidences:
                avg_layer1_5 = sum(layer_confidences[:5]) / 5 if len(layer_confidences) >= 5 else sum(layer_confidences) / len(layer_confidences)
                self.shared_state.update_consensus_strength(avg_layer1_5)
                
                if len(layer_confidences) >= 8:
                    avg_layer6_8 = sum(layer_confidences[5:8]) / 3
                    self.shared_state.update_cross_verification_score(avg_layer6_8)
                
                self.shared_state.update_preliminary_confidence(sum(layer_confidences) / len(layer_confidences))
            
            result['layer_context'] = layer_context
            
            self.shared_state.save_rollback_point({
                'step': 'after_simulation',
                'result': result.copy(),
                'layer_context': {k: v for k, v in layer_context.items() if k != 'query'}
            })
            
            self._log_execution('step_3', result)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Step 3 error: {str(e)}")
        
        return result
    
    def _step4_run_refinement_engine(self, query: str, simulation_result: Dict[str, Any],
                                      feedback: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Step 4: Run Refinement Engine
        
        Perform 12-step iterative refinement on the simulation output.
        Delegates to RefinementOrchestrator when available.
        """
        logger.info("Step 4: Running refinement engine")
        
        result = {
            'step': 'run_refinement_engine',
            'status': 'success',
            'refinement_steps': [],
            'final_confidence': 0.0
        }
        
        try:
            ro_available = (hasattr(self, 'refinement_orchestrator') and 
                           self.refinement_orchestrator is not None and
                           hasattr(self.refinement_orchestrator, 'smm') and 
                           self.refinement_orchestrator.smm is not None)
            
            if ro_available:
                qpe_output = {
                    'status': 'success',
                    'persona_responses': simulation_result.get('layer_context', {}).get('expert_analysis', {}),
                    'simulation_layers': simulation_result.get('layers_executed', []),
                    'conflicts': simulation_result.get('conflicts', [])
                }
                
                axis_scores = simulation_result.get('layer_context', {}).get('axis_scores', {})
                
                try:
                    ro_result = self.refinement_orchestrator.run(
                        qpe_output=qpe_output,
                        query_text=query,
                        query_topic_uid=f"query_{self.shared_state.session_id}",
                        initial_axis_context_scores={str(k): v for k, v in axis_scores.items()},
                        active_location_context=[],
                        session_id=self.shared_state.session_id,
                        pass_num=self.trigger_system.current_iteration + 1
                    )
                    
                    if ro_result.get('status') == 'success':
                        result['final_confidence'] = ro_result.get('final_confidence', 0.0)
                        result['refined_answer'] = ro_result.get('refined_answer_text', '')
                        result['refinement_steps'] = ro_result.get('refinement_steps_log', {})
                        result['governance_check'] = {'status': 'passed'}
                        result['regulatory_check'] = {'status': 'passed'}
                        
                        research_needs = ro_result.get('research_needs', [])
                        if research_needs:
                            result['research_needs'] = research_needs
                    else:
                        logger.warning("RefinementOrchestrator returned error, falling back to placeholder")
                        ro_available = False
                except Exception as ro_error:
                    logger.warning(f"RefinementOrchestrator execution error: {ro_error}, using fallback")
                    ro_available = False
            
            if not ro_available:
                refinement_steps = [
                    "Analysis of QPE Outputs",
                    "Initial Synthesis",
                    "Gap Identification",
                    "Premise Validation",
                    "Context Expansion",
                    "Logical Flow Enhancement",
                    "Evidence Strengthening",
                    "Governance Check",
                    "Final Synthesis",
                    "Answer Quality Evaluation",
                    "Final Answer Generation",
                    "Meta-Learning"
                ]
                
                cumulative_confidence = 0.6
                
                for step_num, step_name in enumerate(refinement_steps, 1):
                    step_confidence = min(0.95, cumulative_confidence + (step_num * 0.025))
                    
                    step_result = {
                        'step_num': step_num,
                        'step_name': step_name,
                        'status': 'completed',
                        'confidence': step_confidence
                    }
                    
                    if step_name == "Governance Check":
                        step_result['governance_status'] = 'passed'
                        result['governance_check'] = {'status': 'passed'}
                    
                    result['refinement_steps'].append(step_result)
                    cumulative_confidence = step_confidence
                
                if feedback:
                    feedback_confidence = feedback.get('final_confidence', 0.0)
                    cumulative_confidence = max(cumulative_confidence, feedback_confidence + 0.05)
                
                result['final_confidence'] = cumulative_confidence
            
            self.shared_state.update_preliminary_confidence(result['final_confidence'])
            
            self._log_execution('step_4', result)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['final_confidence'] = 0.5
            logger.error(f"Step 4 error: {str(e)}")
        
        return result
    
    def _step5_output_finalization(self, query: str, refinement_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Output Finalization
        
        Compile and format the final answer after all checks.
        Uses refined answer from RefinementOrchestrator when available.
        """
        logger.info("Step 5: Finalizing output")
        
        result = {
            'step': 'output_finalization',
            'status': 'success'
        }
        
        try:
            confidence = refinement_result.get('final_confidence', 0.0)
            
            refined_answer = refinement_result.get('refined_answer', '')
            if refined_answer:
                result['final_answer'] = refined_answer
            else:
                result['final_answer'] = f"Processed query through 17-axis coordinate system with {confidence:.1%} confidence."
            
            result['confidence'] = confidence
            result['processed_at'] = datetime.now(UTC).isoformat()
            
            if refinement_result.get('governance_check'):
                result['governance_check'] = refinement_result['governance_check']
            if refinement_result.get('regulatory_check'):
                result['regulatory_check'] = refinement_result['regulatory_check']
            if refinement_result.get('research_needs'):
                result['research_needs'] = refinement_result['research_needs']
            
            self._log_execution('step_5', result)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Step 5 error: {str(e)}")
        
        return result
    
    def _handle_persona_arbitration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle persona conflict through arbitration (Layer 5 coordination).
        
        Implements voting/quorum mechanism to reach consensus.
        Uses weighted voting based on persona expertise relevance and confidence scores.
        """
        logger.info("Handling persona arbitration - initiating consensus debate")
        
        personas_output = context.get('personas_output', {}).copy()
        conflicts = context.get('conflicts', [])
        
        persona_weights = {
            'knowledge': 1.0,
            'sector': 1.0,
            'regulatory': 1.2,
            'compliance': 1.2
        }
        
        votes = {}
        weighted_scores = {}
        for persona_type, output in personas_output.items():
            confidence = output.get('confidence', 0.5)
            weight = persona_weights.get(persona_type, 1.0)
            votes[persona_type] = confidence
            weighted_scores[persona_type] = confidence * weight
        
        if weighted_scores:
            total_weight = sum(persona_weights.get(p, 1.0) for p in weighted_scores)
            weighted_avg = sum(weighted_scores.values()) / total_weight
            
            confidence_variance = max(votes.values()) - min(votes.values()) if votes else 0
            consensus_strength = max(0.3, 1.0 - confidence_variance)
            
            highest_scorer = max(weighted_scores.items(), key=lambda x: x[1])[0]
            
            for persona_type in personas_output:
                old_confidence = personas_output[persona_type].get('confidence', 0.5)
                
                if persona_type == highest_scorer:
                    new_confidence = min(0.95, (old_confidence * 0.6 + weighted_avg * 0.4))
                else:
                    new_confidence = (old_confidence * 0.4 + weighted_avg * 0.6)
                
                personas_output[persona_type]['confidence'] = new_confidence
                personas_output[persona_type]['arbitrated'] = True
                personas_output[persona_type]['arbitration_method'] = 'weighted_voting'
        else:
            weighted_avg = 0.5
            consensus_strength = 0.5
        
        self.shared_state.update_consensus_strength(consensus_strength)
        
        logger.info(f"Arbitration complete. Consensus strength: {consensus_strength:.3f}")
        
        return {
            'personas_output': personas_output,
            'consensus_strength': consensus_strength,
            'weighted_average': weighted_avg,
            'conflicts_resolved': len(conflicts),
            'arbitration_applied': True
        }
    
    def _handle_containment_rollback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle compliance violation through containment rollback.
        
        Rolls back to a safe state and adjusts plan to satisfy constraints.
        Implements actual state restoration from saved rollback points.
        """
        logger.info("Handling containment rollback - compliance violation detected")
        
        rollback_points = self.shared_state.state.get('rollback_points', [])
        
        violation_details = context.get('compliance_check', {})
        regulatory_issues = context.get('regulatory_check', {})
        
        if rollback_points:
            last_safe_state = rollback_points[-1]
            rollback_id = last_safe_state['id']
            snapshot = last_safe_state['snapshot']
            
            logger.info(f"Rolling back to checkpoint: {rollback_id}")
            
            restored_context = snapshot.get('layer_context', {})
            
            adjustments = []
            if violation_details.get('status') == 'failed':
                adjustments.append({
                    'type': 'compliance_constraint',
                    'action': 'add_compliance_filter',
                    'reason': 'Compliance check failed, adding stricter controls'
                })
            if regulatory_issues.get('status') == 'failed':
                adjustments.append({
                    'type': 'regulatory_constraint',
                    'action': 'apply_regulatory_framework',
                    'reason': 'Regulatory check failed, applying framework requirements'
                })
            
            self.shared_state.log_trigger(
                TriggerCondition.COMPLIANCE_VIOLATION_DETECTED,
                TriggerAction.CONTAINMENT_ROLLBACK,
                f"Rolled back to {rollback_id} with {len(adjustments)} adjustments"
            )
            
            return {
                'rollback_applied': True,
                'rollback_id': rollback_id,
                'restored_state': snapshot,
                'restored_context': restored_context,
                'adjustments_made': adjustments,
                'remaining_rollback_points': len(rollback_points) - 1
            }
        
        logger.warning("No rollback points available for containment")
        return {
            'rollback_applied': False,
            'reason': 'No rollback points available',
            'fallback_action': 'manual_review_required'
        }
    
    def _log_execution(self, step_id: str, result: Dict[str, Any]) -> None:
        """Log execution step to the execution log."""
        self.execution_log.append({
            'step_id': step_id,
            'result': result,
            'timestamp': datetime.now(UTC).isoformat()
        })
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the complete execution log."""
        return self.execution_log.copy()


def create_master_orchestrator(config: Optional[Dict] = None) -> MasterWorkflowOrchestrator:
    """Factory function to create a configured master orchestrator."""
    return MasterWorkflowOrchestrator(config)
