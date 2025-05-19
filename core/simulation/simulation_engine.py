"""
Simulation Engine

This module provides the simulation capabilities for the UKG system,
including expert persona simulation and knowledge refinement.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

class SimulationEngine:
    """
    Simulation Engine
    
    This component manages the simulation capabilities of the UKG system,
    including expert role simulation, knowledge refinement, and
    confidence assessment.
    """
    
    def __init__(self, config=None, graph_manager=None, memory_manager=None, ka_engine=None):
        """
        Initialize the Simulation Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager instance
            memory_manager: Memory Manager instance
            ka_engine: Knowledge Algorithm Engine instance
        """
        logging.info(f"[{datetime.now()}] Initializing SimulationEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        self.ka_engine = ka_engine
        
        # Configuration
        self.sim_config = self.config.get('simulation', {})
        self.max_passes = self.sim_config.get('max_simulation_passes', 3)
        self.target_confidence = self.sim_config.get('target_confidence_overall', 0.90)
        
        # Layer 5 Configuration
        self.integration_engine_enabled = self.sim_config.get('enable_layer5_integration', True)
        self.layer5_engine = None
        if self.integration_engine_enabled:
            try:
                from simulation.layer5_integration import Layer5IntegrationEngine
                self.layer5_engine = Layer5IntegrationEngine(
                    config=self.config.get('layer5', {}),
                    system_manager=None  # Will be set later by united_system_manager
                )
                logging.info(f"[{datetime.now()}] Layer 5 Integration Engine initialized")
            except Exception as e:
                logging.error(f"[{datetime.now()}] Failed to initialize Layer 5 Integration Engine: {str(e)}")
                self.integration_engine_enabled = False
        
        # Layer 7 Configuration
        self.agi_simulation_enabled = self.sim_config.get('enable_layer7_agi', True)
        self.layer7_engine = None
        if self.agi_simulation_enabled:
            try:
                from simulation.layer7_agi_system import AGISimulationEngine
                self.layer7_engine = AGISimulationEngine(
                    config=self.config.get('layer7', {}),
                    system_manager=None  # Will be set later by united_system_manager
                )
                logging.info(f"[{datetime.now()}] Layer 7 AGI Simulation Engine initialized with uncertainty threshold 0.15")
            except Exception as e:
                logging.error(f"[{datetime.now()}] Failed to initialize Layer 7 AGI Simulation Engine: {str(e)}")
                self.agi_simulation_enabled = False
        
        # Persona configuration
        self.personas = {
            'knowledge': {
                'enabled': True,
                'weight': 1.0,
                'components': ['job_role', 'education', 'certifications', 'skills', 'training', 'career_path', 'related_jobs']
            },
            'sector': {
                'enabled': True,
                'weight': 1.0,
                'components': ['job_role', 'education', 'certifications', 'skills', 'training', 'career_path', 'related_jobs']
            },
            'regulatory': {
                'enabled': True,
                'weight': 1.0,
                'components': ['job_role', 'education', 'certifications', 'skills', 'training', 'career_path', 'related_jobs']
            },
            'compliance': {
                'enabled': True,
                'weight': 1.0,
                'components': ['job_role', 'education', 'certifications', 'skills', 'training', 'career_path', 'related_jobs']
            }
        }
        
        # Override with config if provided
        personas_config = self.sim_config.get('personas')
        if personas_config:
            for persona_id, persona_config in personas_config.items():
                if persona_id in self.personas:
                    self.personas[persona_id].update(persona_config)
        
        # Active simulations
        self.active_simulations = {}
        
        # Layer configuration
        self.layer_config = self.sim_config.get('layers', {})
        self.pov_engine_enabled = self.layer_config.get('pov_engine_enabled', True)
        self.integration_engine_enabled = self.layer_config.get('integration_engine_enabled', True)
        
        # Initialize Layer 5 Integration Engine if enabled
        self.layer5_engine = None
        if self.integration_engine_enabled:
            try:
                from simulation.layer5_integration import Layer5IntegrationEngine
                self.layer5_engine = Layer5IntegrationEngine(
                    config=self.layer_config.get('layer5', {}),
                    system_manager=None  # Will be set later if system manager is provided
                )
                logging.info(f"[{datetime.now()}] Layer 5 Integration Engine initialized")
            except ImportError as e:
                logging.warning(f"[{datetime.now()}] Failed to import Layer 5 Integration Engine: {e}")
                self.integration_engine_enabled = False
        
        # Stats
        self.stats = {
            'simulations_started': 0,
            'simulations_completed': 0,
            'passes_executed': 0,
            'average_confidence': 0.0
        }
        
        logging.info(f"[{datetime.now()}] SimulationEngine initialized")
    
    def start_simulation(self, query: str, context: Optional[Dict] = None, 
                       session_id: Optional[str] = None, 
                       simulation_params: Optional[Dict] = None) -> Dict:
        """
        Start a new simulation.
        
        Args:
            query: User query or input
            context: Optional context information
            session_id: Optional session ID
            simulation_params: Optional simulation parameters
            
        Returns:
            dict: Simulation record
        """
        # Generate simulation ID
        sim_id = f"SIM_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        # Prepare simulation parameters
        params = {
            'max_passes': self.max_passes,
            'target_confidence': self.target_confidence,
            'personas': self.personas.copy()
        }
        
        # Update with custom parameters if provided
        if simulation_params:
            if 'max_passes' in simulation_params:
                params['max_passes'] = simulation_params['max_passes']
            if 'target_confidence' in simulation_params:
                params['target_confidence'] = simulation_params['target_confidence']
            if 'personas' in simulation_params:
                for persona_id, persona_config in simulation_params['personas'].items():
                    if persona_id in params['personas']:
                        params['personas'][persona_id].update(persona_config)
        
        # Create simulation record
        simulation = {
            'simulation_id': sim_id,
            'session_id': session_id,
            'query': query,
            'context': context or {},
            'params': params,
            'status': 'started',
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_ms': None,
            'passes': [],
            'current_pass': 0,
            'results': None,
            'confidence': {
                'overall': 0.0,
                'knowledge': 0.0,
                'sector': 0.0,
                'regulatory': 0.0,
                'compliance': 0.0
            },
            'error': None
        }
        
        # Add to active simulations
        self.active_simulations[sim_id] = simulation
        
        # Update stats
        self.stats['simulations_started'] += 1
        
        logging.info(f"[{datetime.now()}] Started simulation {sim_id}")
        
        return simulation
    
    def get_simulation(self, simulation_id: str) -> Optional[Dict]:
        """
        Get a simulation by ID.
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            dict: Simulation record or None if not found
        """
        return self.active_simulations.get(simulation_id)
        
    def _apply_layer5_integration(self, context: Dict, simulation_id: str) -> Dict:
        """
        Apply Layer 5 Integration Engine processing to a simulation context.
        
        Args:
            simulation_id: ID of the simulation
            context: Simulation context with results from Layers 1-4
            
        Returns:
            dict: Enhanced context with Layer 5 integration
        """
        # Skip if Layer 5 is not enabled
        if not self.integration_engine_enabled or not self.layer5_engine:
            logging.info(f"[{datetime.now()}] Layer 5 integration skipped for {simulation_id}")
            return context
            
        # Get simulation details
        simulation = self.active_simulations.get(simulation_id)
        if not simulation:
            logging.warning(f"[{datetime.now()}] Cannot apply Layer 5 integration - simulation {simulation_id} not found")
            return context
            
        # Check for gatekeeper decision
        current_pass = simulation.get('current_pass', 1)
        gatekeeper_decision = context.get('gatekeeper_decision', {})
        layer5_activation = gatekeeper_decision.get('layer_activations', {}).get('layer_5', {})
        
        # Skip if gatekeeper says no activation needed
        if not layer5_activation.get('activate', False):
            logging.info(f"[{datetime.now()}] Layer 5 integration not activated by gatekeeper for {simulation_id}")
            return context
            
        try:
            # Get Layer 5 parameters from gatekeeper if available
            layer5_params = None
            if 'gatekeeper' in context and hasattr(context['gatekeeper'], 'get_layer5_integration_parameters'):
                gatekeeper = context['gatekeeper']
                layer5_params = gatekeeper.get_layer5_integration_parameters(context)
                
            # Process through Layer 5 Integration Engine
            logging.info(f"[{datetime.now()}] Processing simulation {simulation_id} through Layer 5 Integration Engine")
            start_time = datetime.now()
            
            integrated_context = self.layer5_engine.process(context, layer5_params)
            
            # Track performance
            processing_time = (datetime.now() - start_time).total_seconds()
            logging.info(f"[{datetime.now()}] Layer 5 integration complete for {simulation_id} in {processing_time:.2f}s")
            
            # Update metrics
            confidence_before = context.get('confidence_score', 0.0)
            confidence_after = integrated_context.get('confidence_score', confidence_before)
            confidence_delta = max(0, confidence_after - confidence_before)
            
            # Log improvement
            if confidence_delta > 0:
                logging.info(f"[{datetime.now()}] Layer 5 improved confidence for {simulation_id} by {confidence_delta:.4f}")
                
            return integrated_context
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Layer 5 integration error for {simulation_id}: {str(e)}")
            # Return original context on error
            return context
    
    def run_simulation_pass(self, simulation_id: str) -> Dict:
        """
        Run a single pass of the simulation.
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            dict: Updated simulation record
        """
        # Get simulation
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return {'error': f"Simulation with ID {simulation_id} not found"}
        
        # Check if simulation is already completed
        if simulation['status'] in ('completed', 'failed', 'cancelled'):
            return simulation
        
        # Increment pass counter
        current_pass = simulation['current_pass'] + 1
        simulation['current_pass'] = current_pass
        
        # Create pass record
        pass_record = {
            'pass_number': current_pass,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_ms': None,
            'persona_results': {},
            'confidence': {
                'overall': 0.0,
                'knowledge': 0.0,
                'sector': 0.0,
                'regulatory': 0.0,
                'compliance': 0.0
            },
            'synthesis': None,
            'status': 'started'
        }
        
        try:
            # Record start time for duration calculation
            pass_start_time = datetime.now()
            
            # Run each enabled persona
            for persona_id, persona_config in simulation['params']['personas'].items():
                if persona_config['enabled']:
                    # Run persona simulation
                    persona_result = self._run_persona_simulation(
                        persona_id=persona_id,
                        query=simulation['query'],
                        context=simulation['context'],
                        simulation_id=simulation_id,
                        pass_number=current_pass
                    )
                    
                    # Add to pass record
                    pass_record['persona_results'][persona_id] = persona_result
                    
                    # Update confidence
                    pass_record['confidence'][persona_id] = persona_result.get('confidence', 0.0)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(pass_record['confidence'])
            pass_record['confidence']['overall'] = overall_confidence
            
            # Synthesize results
            synthesis = self._synthesize_results(
                pass_record['persona_results'],
                simulation['query'],
                simulation['context'],
                current_pass
            )
            
            # Create context object for gatekeeper and Layer 5
            context = {
                'simulation_id': simulation_id,
                'simulation_pass': current_pass,
                'query': simulation['query'],
                'context': simulation['context'],
                'persona_results': pass_record['persona_results'],
                'synthesis': synthesis,
                'confidence_score': overall_confidence,
                'confidence': pass_record['confidence'],
                'uncertainty_level': max(0.0, 1.0 - overall_confidence),
                'entropy_score': 0.0  # Will be calculated in future implementation
            }
            
            # Create or use existing Gatekeeper Agent
            from simulation.gatekeeper_agent import GatekeeperAgent
            gatekeeper = GatekeeperAgent()
            
            # Pass through Gatekeeper to determine layer activation
            gatekeeper_decision = gatekeeper.evaluate(context)
            context['gatekeeper_decision'] = gatekeeper_decision
            context['gatekeeper'] = gatekeeper
            
            # Check if we need to apply Layer 5 integration (from Gatekeeper)
            layer5_active = False
            if self.integration_engine_enabled and self.layer5_engine:
                if 'layer_5' in gatekeeper_decision.get('layer_activations', {}):
                    layer5_active = gatekeeper_decision['layer_activations']['layer_5'].get('activate', False)
            
            # Apply Layer 5 integration if activated
            if layer5_active:
                logging.info(f"[{datetime.now()}] Layer 5 Integration Engine activated for simulation {simulation_id}, pass {current_pass}")
                enhanced_context = self._apply_layer5_integration(context, simulation_id)
                
                # Update synthesis with enhanced content if available
                if 'content' in enhanced_context and enhanced_context['content']:
                    synthesis['content'] = enhanced_context['content']
                
                # Update confidence scores if improved
                if 'confidence_score' in enhanced_context:
                    new_confidence = enhanced_context['confidence_score']
                    
            # Check if we need to apply Layer 7 AGI simulation (from Gatekeeper)
            layer7_active = False
            if self.agi_simulation_enabled and self.layer7_engine:
                if 'layer_7' in gatekeeper_decision.get('layer_activations', {}):
                    layer7_active = gatekeeper_decision['layer_activations']['layer_7'].get('activate', False)
            
            # Apply Layer 7 AGI simulation if activated
            if layer7_active:
                logging.info(f"[{datetime.now()}] Layer 7 AGI Simulation Engine activated for simulation {simulation_id}, pass {current_pass}")
                agi_context = self._apply_layer7_agi_processing(context, simulation_id)
                
                # Update synthesis with AGI-enhanced content if available
                if 'content' in agi_context and agi_context['content']:
                    synthesis['content'] = agi_context['content']
                
                # Update synthesis with layer7 metadata
                synthesis['layer7_applied'] = True
                if 'layer7_processing_details' in agi_context:
                    synthesis['layer7_processing_details'] = agi_context['layer7_processing_details']
                    
                # Record any emergent properties detected
                if 'emergence_score' in agi_context:
                    synthesis['emergence_score'] = agi_context['emergence_score']
                
                # Update confidence scores - note that AGI can reduce confidence
                if 'confidence_score' in agi_context:
                    new_confidence = agi_context['confidence_score']
                    old_confidence = overall_confidence
                    
                    if new_confidence > old_confidence:
                        logging.info(f"[{datetime.now()}] Layer 5 improved confidence from {old_confidence:.4f} to {new_confidence:.4f}")
                        overall_confidence = new_confidence
                        pass_record['confidence']['overall'] = overall_confidence
                
                # Add Layer 5 metadata to synthesis
                synthesis['layer5_applied'] = True
                synthesis['layer5_enhancements'] = enhanced_context.get('layer5_enhancements', [])
                synthesis['layer5_processing_type'] = enhanced_context.get('layer5_processing_type', 'none')
            else:
                logging.info(f"[{datetime.now()}] Layer 5 Integration not activated for simulation {simulation_id}, pass {current_pass}")
                synthesis['layer5_applied'] = False
            
            pass_record['synthesis'] = synthesis
            
            # Calculate duration
            pass_end_time = datetime.now()
            duration_ms = (pass_end_time - pass_start_time).total_seconds() * 1000
            pass_record['duration_ms'] = duration_ms
            pass_record['end_time'] = pass_end_time.isoformat()
            
            # Update pass status
            pass_record['status'] = 'completed'
            
            # Add pass to simulation
            simulation['passes'].append(pass_record)
            
            # Update simulation confidence
            simulation['confidence'] = pass_record['confidence'].copy()
            
            # Check if we've reached target confidence
            if overall_confidence >= simulation['params']['target_confidence']:
                simulation['status'] = 'completed'
                simulation['end_time'] = datetime.now().isoformat()
                simulation['duration_ms'] = (datetime.fromisoformat(simulation['end_time']) - 
                                           datetime.fromisoformat(simulation['start_time'])).total_seconds() * 1000
                simulation['results'] = synthesis
                
                # Update stats
                self.stats['simulations_completed'] += 1
                self.stats['passes_executed'] += current_pass
                
                # Update average confidence
                total_confidence = self.stats['average_confidence'] * (self.stats['simulations_completed'] - 1)
                self.stats['average_confidence'] = (total_confidence + overall_confidence) / self.stats['simulations_completed']
                
                logging.info(f"[{datetime.now()}] Simulation {simulation_id} completed with confidence {overall_confidence:.2f}")
            
            # Check if we've reached max passes
            elif current_pass >= simulation['params']['max_passes']:
                simulation['status'] = 'completed'
                simulation['end_time'] = datetime.now().isoformat()
                simulation['duration_ms'] = (datetime.fromisoformat(simulation['end_time']) - 
                                           datetime.fromisoformat(simulation['start_time'])).total_seconds() * 1000
                simulation['results'] = synthesis
                
                # Update stats
                self.stats['simulations_completed'] += 1
                self.stats['passes_executed'] += current_pass
                
                # Update average confidence
                total_confidence = self.stats['average_confidence'] * (self.stats['simulations_completed'] - 1)
                self.stats['average_confidence'] = (total_confidence + overall_confidence) / self.stats['simulations_completed']
                
                logging.info(f"[{datetime.now()}] Simulation {simulation_id} completed with max passes reached")
                
        except Exception as e:
            # Record error
            pass_record['status'] = 'failed'
            pass_record['end_time'] = datetime.now().isoformat()
            
            if pass_start_time:
                pass_record['duration_ms'] = (datetime.fromisoformat(pass_record['end_time']) - 
                                            pass_start_time).total_seconds() * 1000
            
            # Add pass to simulation
            simulation['passes'].append(pass_record)
            
            # Update simulation status
            simulation['status'] = 'failed'
            simulation['end_time'] = datetime.now().isoformat()
            simulation['error'] = str(e)
            
            if simulation['start_time']:
                simulation['duration_ms'] = (datetime.fromisoformat(simulation['end_time']) - 
                                           datetime.fromisoformat(simulation['start_time'])).total_seconds() * 1000
            
            logging.error(f"[{datetime.now()}] Error in simulation {simulation_id}: {str(e)}")
        
        return simulation
    
    def _run_persona_simulation(self, persona_id: str, query: str, context: Dict,
                              simulation_id: str, pass_number: int) -> Dict:
        """
        Run simulation for a specific persona.
        
        Args:
            persona_id: Persona ID
            query: User query
            context: Context information
            simulation_id: Simulation ID
            pass_number: Current pass number
            
        Returns:
            dict: Persona simulation results
        """
        # Create persona result record
        result = {
            'persona_id': persona_id,
            'simulation_id': simulation_id,
            'pass_number': pass_number,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_ms': None,
            'components': {},
            'response': None,
            'confidence': 0.0,
            'status': 'started'
        }
        
        try:
            start_time = datetime.now()
            
            # Get persona configuration
            simulation = self.active_simulations[simulation_id]
            persona_config = simulation['params']['personas'][persona_id]
            
            # Process each component
            component_confidences = []
            for component_id in persona_config['components']:
                # Run component simulation
                component_result = self._run_component_simulation(
                    persona_id=persona_id,
                    component_id=component_id,
                    query=query,
                    context=context,
                    simulation_id=simulation_id,
                    pass_number=pass_number
                )
                
                # Add to result
                result['components'][component_id] = component_result
                
                # Add confidence to list for averaging
                component_confidences.append(component_result.get('confidence', 0.0))
            
            # Calculate overall persona confidence
            if component_confidences:
                result['confidence'] = sum(component_confidences) / len(component_confidences)
            
            # Generate response by combining components
            response = self._generate_persona_response(
                persona_id=persona_id,
                components=result['components'],
                query=query,
                context=context
            )
            
            result['response'] = response
            
            # Calculate duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            result['duration_ms'] = duration_ms
            result['end_time'] = end_time.isoformat()
            
            # Update status
            result['status'] = 'completed'
            
        except Exception as e:
            # Record error
            result['status'] = 'failed'
            result['end_time'] = datetime.now().isoformat()
            result['error'] = str(e)
            
            if 'start_time' in locals():
                result['duration_ms'] = (datetime.fromisoformat(result['end_time']) - 
                                       start_time).total_seconds() * 1000
            
            logging.error(f"[{datetime.now()}] Error in persona simulation {persona_id}: {str(e)}")
        
        return result
    
    def _run_component_simulation(self, persona_id: str, component_id: str, 
                                query: str, context: Dict,
                                simulation_id: str, pass_number: int) -> Dict:
        """
        Run simulation for a specific persona component.
        
        Args:
            persona_id: Persona ID
            component_id: Component ID
            query: User query
            context: Context information
            simulation_id: Simulation ID
            pass_number: Current pass number
            
        Returns:
            dict: Component simulation results
        """
        # Create component result record
        result = {
            'persona_id': persona_id,
            'component_id': component_id,
            'simulation_id': simulation_id,
            'pass_number': pass_number,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_ms': None,
            'response': None,
            'confidence': 0.0,
            'status': 'started'
        }
        
        try:
            start_time = datetime.now()
            
            # Prepare KA execution parameters
            ka_params = {
                'persona_id': persona_id,
                'component_id': component_id,
                'query': query,
                'context': context,
                'simulation_id': simulation_id,
                'pass_number': pass_number
            }
            
            # Determine which KA to execute based on persona and component
            ka_id = f"KA_PERSONA_{persona_id.upper()}_{component_id.upper()}"
            
            # Execute KA if available
            if self.ka_engine and ka_id in self.ka_engine.list_algorithms():
                # Execute algorithm
                execution = self.ka_engine.execute_algorithm(
                    ka_id=ka_id,
                    params=ka_params,
                    session_id=simulation_id
                )
                
                if execution['status'] == 'completed':
                    # Extract results
                    ka_results = execution.get('results', {})
                    result['response'] = ka_results.get('response')
                    result['confidence'] = ka_results.get('confidence', 0.6)
                    result['ka_execution_id'] = execution['execution_id']
                else:
                    # KA execution failed, use fallback
                    result['response'] = self._generate_fallback_response(persona_id, component_id, query)
                    result['confidence'] = 0.4
                    result['ka_execution_failed'] = True
            else:
                # No KA available, use fallback
                result['response'] = self._generate_fallback_response(persona_id, component_id, query)
                result['confidence'] = 0.4
                result['ka_not_available'] = True
            
            # Calculate duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            result['duration_ms'] = duration_ms
            result['end_time'] = end_time.isoformat()
            
            # Update status
            result['status'] = 'completed'
            
        except Exception as e:
            # Record error
            result['status'] = 'failed'
            result['end_time'] = datetime.now().isoformat()
            result['error'] = str(e)
            
            if 'start_time' in locals():
                result['duration_ms'] = (datetime.fromisoformat(result['end_time']) - 
                                       start_time).total_seconds() * 1000
            
            logging.error(f"[{datetime.now()}] Error in component simulation {persona_id}/{component_id}: {str(e)}")
        
        return result
    
    def _generate_persona_response(self, persona_id: str, components: Dict, 
                                 query: str, context: Dict) -> Dict:
        """
        Generate a combined response for a persona from its components.
        
        Args:
            persona_id: Persona ID
            components: Component results
            query: User query
            context: Context information
            
        Returns:
            dict: Combined response
        """
        # Basic combination - could be enhanced with more sophisticated approach
        combined_response = {
            'persona_id': persona_id,
            'perspective': f"{persona_id.capitalize()} Expert",
            'content': ""
        }
        
        # Get component responses
        component_contents = []
        for component_id, component in components.items():
            if component.get('status') == 'completed' and component.get('response'):
                response_content = component['response'].get('content', '')
                if response_content:
                    component_contents.append(f"[{component_id.capitalize()}] {response_content}")
        
        # Combine content
        if component_contents:
            combined_response['content'] = "\n\n".join(component_contents)
        else:
            combined_response['content'] = f"No {persona_id.capitalize()} Expert response available."
        
        return combined_response
    
    def _generate_fallback_response(self, persona_id: str, component_id: str, query: str) -> Dict:
        """
        Generate a fallback response when KA execution fails.
        
        Args:
            persona_id: Persona ID
            component_id: Component ID
            query: User query
            
        Returns:
            dict: Fallback response
        """
        fallback_responses = {
            'knowledge': {
                'job_role': {
                    'content': "As a Knowledge Expert, I would approach this from the perspective of maintaining comprehensive understanding of the subject domain."
                },
                'education': {
                    'content': "Education in knowledge management and information science would suggest organizing this information systematically."
                }
            },
            'sector': {
                'job_role': {
                    'content': "From a sector expertise perspective, industry standards and current market trends would inform this analysis."
                },
                'education': {
                    'content': "Sector-specific education emphasizes practical applications and industry-specific knowledge frameworks."
                }
            },
            'regulatory': {
                'job_role': {
                    'content': "As a Regulatory Expert, compliance with relevant standards and regulations is essential in this context."
                },
                'education': {
                    'content': "Regulatory education focuses on understanding legislative frameworks and their practical implications."
                }
            },
            'compliance': {
                'job_role': {
                    'content': "From a compliance perspective, ensuring adherence to policies while maintaining operational efficiency is key."
                },
                'education': {
                    'content': "Compliance education emphasizes risk management and governance frameworks applicable to this situation."
                }
            }
        }
        
        # Get fallback response if available
        if (persona_id in fallback_responses and 
            component_id in fallback_responses[persona_id]):
            response = fallback_responses[persona_id][component_id].copy()
        else:
            # Generic fallback
            response = {
                'content': f"From the {persona_id.capitalize()} {component_id.capitalize()} perspective, a structured analysis would help address this query."
            }
        
        # Add metadata
        response['persona_id'] = persona_id
        response['component_id'] = component_id
        response['is_fallback'] = True
        
        return response
    
    def _calculate_overall_confidence(self, confidences: Dict) -> float:
        """
        Calculate overall confidence from individual confidence scores.
        
        Args:
            confidences: Dictionary of confidence scores
            
        Returns:
            float: Overall confidence score
        """
        # Exclude 'overall' key if present
        relevant_confidences = {k: v for k, v in confidences.items() if k != 'overall'}
        
        if not relevant_confidences:
            return 0.0
        
        # Simple average for now - could be enhanced with weighted approach
        return sum(relevant_confidences.values()) / len(relevant_confidences)
    
    def _synthesize_results(self, persona_results: Dict, query: str, 
                          context: Dict, pass_number: int) -> Dict:
        """
        Synthesize results from all personas.
        
        Args:
            persona_results: Results from all personas
            query: User query
            context: Context information
            pass_number: Current pass number
            
        Returns:
            dict: Synthesized results
        """
        # Create synthesis record
        synthesis = {
            'pass_number': pass_number,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'content': "",
            'perspectives': [],
            'confidence': 0.0
        }
        
        # Collect persona responses
        for persona_id, result in persona_results.items():
            if result.get('status') == 'completed' and result.get('response'):
                synthesis['perspectives'].append({
                    'persona_id': persona_id,
                    'perspective': result['response'].get('perspective', f"{persona_id.capitalize()} Expert"),
                    'content': result['response'].get('content', ''),
                    'confidence': result.get('confidence', 0.0)
                })
        
        # Generate combined content
        if synthesis['perspectives']:
            # Create sections for each perspective
            sections = []
            for perspective in synthesis['perspectives']:
                sections.append(f"## {perspective['perspective']} Perspective\n\n{perspective['content']}")
            
            # Create summary section
            summary = "## Summary\n\n"
            summary += "This analysis combines multiple expert perspectives to provide a comprehensive response.\n\n"
            
            # Combine all sections
            synthesis['content'] = f"{summary}\n\n" + "\n\n".join(sections)
            
            # Calculate confidence
            perspective_confidences = [p['confidence'] for p in synthesis['perspectives']]
            if perspective_confidences:
                synthesis['confidence'] = sum(perspective_confidences) / len(perspective_confidences)
        else:
            synthesis['content'] = "No expert perspectives were available to analyze this query."
            synthesis['confidence'] = 0.0
        
        return synthesis
    
    def cancel_simulation(self, simulation_id: str) -> Dict:
        """
        Cancel an active simulation.
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            dict: Updated simulation record
        """
        # Get simulation
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return {'error': f"Simulation with ID {simulation_id} not found"}
        
        # Check if already completed
        if simulation['status'] in ('completed', 'failed', 'cancelled'):
            return simulation
        
        # Update status
        simulation['status'] = 'cancelled'
        simulation['end_time'] = datetime.now().isoformat()
        
        if simulation['start_time']:
            simulation['duration_ms'] = (datetime.fromisoformat(simulation['end_time']) - 
                                       datetime.fromisoformat(simulation['start_time'])).total_seconds() * 1000
        
        logging.info(f"[{datetime.now()}] Simulation {simulation_id} cancelled")
        
        return simulation
    
    def run_simulation(self, query: str, context: Optional[Dict] = None, 
                    session_id: Optional[str] = None, 
                    simulation_params: Optional[Dict] = None) -> Dict:
        """
        Run a complete simulation (all passes).
        
        Args:
            query: User query or input
            context: Optional context information
            session_id: Optional session ID
            simulation_params: Optional simulation parameters
            
        Returns:
            dict: Final simulation record
        """
        # Start the simulation
        simulation = self.start_simulation(
            query=query,
            context=context,
            session_id=session_id,
            simulation_params=simulation_params
        )
        
        simulation_id = simulation['simulation_id']
        
        # Run passes until complete
        while simulation['status'] == 'started':
            simulation = self.run_simulation_pass(simulation_id)
        
        return simulation
    
    def run_single_persona_simulation(self, persona_id: str, query: str, 
                                   context: Optional[Dict] = None,
                                   session_id: Optional[str] = None) -> Dict:
        """
        Run a simulation with only a single persona.
        
        Args:
            persona_id: Persona ID to use
            query: User query or input
            context: Optional context information
            session_id: Optional session ID
            
        Returns:
            dict: Simulation results
        """
        # Create simulation parameters with only one persona enabled
        simulation_params = {
            'personas': {
                'knowledge': {'enabled': False},
                'sector': {'enabled': False},
                'regulatory': {'enabled': False},
                'compliance': {'enabled': False}
            },
            'max_passes': 1
        }
        
        # Enable the requested persona
        if persona_id in simulation_params['personas']:
            simulation_params['personas'][persona_id]['enabled'] = True
        else:
            return {'error': f"Invalid persona ID: {persona_id}"}
        
        # Run the simulation
        simulation = self.run_simulation(
            query=query,
            context=context,
            session_id=session_id,
            simulation_params=simulation_params
        )
        
        # Extract results for the single persona if available
        if simulation['status'] == 'completed' and simulation['passes']:
            last_pass = simulation['passes'][-1]
            persona_results = last_pass.get('persona_results', {}).get(persona_id)
            
            if persona_results:
                return {
                    'simulation_id': simulation['simulation_id'],
                    'persona_id': persona_id,
                    'query': query,
                    'response': persona_results.get('response'),
                    'confidence': persona_results.get('confidence', 0.0),
                    'duration_ms': simulation.get('duration_ms')
                }
        
        # Return full simulation if persona results not available
        return simulation