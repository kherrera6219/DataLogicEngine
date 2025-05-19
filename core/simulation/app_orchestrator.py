import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
from core.simulation.location_context_engine import LocationContextEngine

class AppOrchestrator:
    """
    The AppOrchestrator is the main coordinator of the UKG system. It manages the entire
    workflow from query receipt to final answer generation, coordinating the various
    components and managing the simulation passes.
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager, simulation_engine, ka_loader):
        """
        Initialize the AppOrchestrator.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager (GraphManager): Reference to the GraphManager
            memory_manager (StructuredMemoryManager): Reference to the StructuredMemoryManager
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
            simulation_engine (SimulationEngine): Reference to the SimulationEngine
            ka_loader (KALoader): Reference to the KALoader
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.simulation_engine = simulation_engine
        self.ka_loader = ka_loader
        self.location_context_engine = None
        
        # Get orchestration configuration
        self.max_passes = self.config.get('max_simulation_passes', 3)
        self.target_confidence = self.config.get('target_confidence_overall', 0.90)
        self.enable_gatekeeper = self.config.get('enable_gatekeeper', True)
        self.layer_progression = self.config.get('layer_progression', [1, 2, 3])
        
        # Initialize LocationContextEngine for Axis 12 location awareness
        self._initialize_location_context_engine()
        
        logging.info(f"[{datetime.now()}] AppOrchestrator initialized with max_passes={self.max_passes}, target_confidence={self.target_confidence}")
        
    def _initialize_location_context_engine(self):
        """Initialize the LocationContextEngine for Axis 12 location awareness."""
        logging.info(f"[{datetime.now()}] Initializing LocationContextEngine (Axis 12)...")
        axis12_conf = self.config.get('axis12_location_logic', {})
        if self.gm and self.usm:  # LocationContextEngine needs GM & USM
            self.location_context_engine = LocationContextEngine(
                config=self.config,
                graph_manager=self.gm,
                united_system_manager=self.usm
            )
            logging.info(f"[{datetime.now()}] LocationContextEngine successfully initialized")
        else:
            logging.error(f"[{datetime.now()}] ERROR: Dependencies missing for LocationContextEngine. Not initialized.")
    
    def process_request(self, query_text: str, target_confidence: float = None) -> Dict[str, Any]:
        """
        Process a user request through the UKG system.
        
        Args:
            query_text (str): The user's query text
            target_confidence (float, optional): Target confidence level, overrides default
            
        Returns:
            dict: Final result package
        """
        # Generate a session ID
        session_id = str(uuid.uuid4())
        
        # Set target confidence (use parameter if provided, otherwise use config default)
        if target_confidence is not None:
            self.target_confidence = target_confidence
        
        logging.info(f"[{datetime.now()}] AO: Starting new session {session_id[:8]}... for query: '{query_text[:50]}...'")
        
        # Initial processing with KA01 and KA02 for query analysis and axis scoring
        initial_ka_outputs = self._run_initial_kas(query_text, session_id)
        
        # Create a normalized query (simplified version for processing)
        normalized_query = query_text.strip().lower()
        
        # Determine active location context for the query
        active_location_uids = []
        if self.location_context_engine:
            logging.info(f"[{datetime.now()}] AppOrch: Determining active location context for session {session_id}...")
            active_location_uids = self.location_context_engine.determine_active_location_context(
                query_text=query_text  # Pass raw query to LocationContextEngine
            )
            
            # Get applicable regulatory frameworks for the active locations
            applicable_reg_uids = []
            if active_location_uids:
                applicable_reg_uids = self.location_context_engine.get_applicable_regulations_for_locations(
                    active_location_uids
                )
                logging.info(f"[{datetime.now()}] AppOrch: Found {len(applicable_reg_uids)} applicable regulatory frameworks.")
        
        # Initialize the simulation data structure
        simulation_data = {
            "session_id": session_id,
            "original_query": query_text,
            "normalized_query": normalized_query,
            "current_pass": 0,
            "target_confidence": self.target_confidence,
            "current_confidence": 0.0,
            "initial_ka_outputs": initial_ka_outputs,
            "active_location_context_uids": active_location_uids,  # Store location context
            "applicable_regulatory_framework_uids": applicable_reg_uids if 'applicable_reg_uids' in locals() else [],
            "history": [],
            "status": "in_progress"
        }
        
        # Run simulation passes until termination conditions are met
        while simulation_data["current_pass"] < self.max_passes:
            simulation_data["current_pass"] += 1
            
            # Process the current pass
            simulation_data = self._process_pass(simulation_data)
            
            # Log history of this pass
            self._log_pass_to_history(simulation_data)
            
            # Check termination conditions
            if self._check_termination_conditions(simulation_data):
                break
        
        # Compile the final answer
        final_answer_package = self._compile_final_answer(simulation_data)
        
        # Log the completion of the session
        logging.info(f"[{datetime.now()}] AO: Completed session {session_id[:8]}... with status: {simulation_data['status']}, final confidence: {simulation_data.get('current_confidence', 0.0):.3f}")
        
        return final_answer_package
    
    def _run_initial_kas(self, query_text: str, session_id: str) -> Dict[str, Any]:
        """
        Run initial Knowledge Algorithms to analyze the query.
        
        Args:
            query_text (str): The user's query text
            session_id (str): The session ID
            
        Returns:
            dict: Results from initial KAs
        """
        logging.info(f"[{datetime.now()}] AO: Running initial KAs for query analysis")
        
        initial_ka_outputs = {}
        
        # Run KA01: Query Analyzer
        ka01_input = {'query_text': query_text}
        ka01_result = self.ka_loader.execute_ka(
            ka_id=1,
            input_data=ka01_input,
            session_id=session_id,
            pass_num=0,  # Special pass number 0 for initial KAs
            layer_num=0   # Special layer number 0 for initial KAs
        )
        
        initial_ka_outputs['ka01'] = ka01_result
        
        # Run KA02: Axis Scorer
        if ka01_result.get('status') == 'success':
            ka02_input = {
                'query_text': query_text,
                'ka01_output': ka01_result
            }
            ka02_result = self.ka_loader.execute_ka(
                ka_id=2,
                input_data=ka02_input,
                session_id=session_id,
                pass_num=0,
                layer_num=0
            )
            
            initial_ka_outputs['ka02'] = ka02_result
        
        # In a full implementation, more initial KAs could be run here
        
        return initial_ka_outputs
    
    def _process_pass(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a simulation pass.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data
        """
        pass_num = simulation_data["current_pass"]
        session_id = simulation_data["session_id"]
        
        logging.info(f"[{datetime.now()}] AO: Processing pass {pass_num} for session {session_id[:8]}...")
        
        # Create a log entry for the start of this pass
        self.smm.add_memory_entry(
            session_id=session_id,
            pass_num=pass_num,
            layer_num=0,  # Special layer number 0 for orchestrator
            entry_type='pass_start',
            content={
                'pass_num': pass_num,
                'start_time': datetime.now().isoformat(),
                'current_confidence': simulation_data.get('current_confidence', 0.0)
            },
            confidence=simulation_data.get('current_confidence', 0.5)
        )
        
        try:
            # Run Layers 1-3 (always run these)
            simulation_data = self.simulation_engine.run_layers_1_3(simulation_data)
            
            # Determine if higher layers should be run
            run_higher_layers = False
            max_layer = 3  # Default to just running Layers 1-3
            
            if self.enable_gatekeeper:
                # In a full implementation, this would be a more sophisticated check
                # For simplicity, just check if confidence is still below target
                run_higher_layers = simulation_data.get('current_confidence', 0.0) < self.target_confidence
                
                # Log the gatekeeper decision
                logging.info(f"[{datetime.now()}] AO: Gatekeeper decision for session {session_id[:8]}, pass {pass_num}: run_higher_layers={run_higher_layers}")
            else:
                # If gatekeeper is disabled, always run higher layers
                run_higher_layers = True
            
            if run_higher_layers and len(self.layer_progression) > 3:
                # Find the maximum layer to run
                max_layer = max(self.layer_progression)
                
                # Run higher layers up to max_layer
                simulation_data = self.simulation_engine.run_layers_up_to(simulation_data, max_layer)
            
            # Log the completion of this pass
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=0,
                entry_type='pass_complete',
                content={
                    'pass_num': pass_num,
                    'max_layer_run': max_layer,
                    'end_time': datetime.now().isoformat(),
                    'current_confidence': simulation_data.get('current_confidence', 0.0)
                },
                confidence=simulation_data.get('current_confidence', 0.5)
            )
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error processing pass {pass_num}: {str(e)}"
            logging.error(f"[{datetime.now()}] AO: {error_msg}", exc_info=True)
            
            # Update simulation data with error status
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            # Log the error
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=0,
                entry_type='pass_error',
                content={
                    'pass_num': pass_num,
                    'error': error_msg,
                    'end_time': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            return simulation_data
    
    def _log_pass_to_history(self, simulation_data: Dict[str, Any]) -> None:
        """
        Log the current pass to the session history.
        
        Args:
            simulation_data (dict): Current simulation data
        """
        pass_num = simulation_data["current_pass"]
        
        # Create a summary of this pass
        pass_summary = {
            'pass_num': pass_num,
            'confidence': simulation_data.get('current_confidence', 0.0),
            'layer_outputs': {}
        }
        
        # Add layer outputs to the summary
        for layer in range(1, 10):  # Up to Layer 9 (adjust as needed)
            layer_key = f"layer{layer}_output"
            if layer_key in simulation_data:
                # Just store the status and other key details, not the full output
                layer_output = simulation_data[layer_key]
                pass_summary['layer_outputs'][layer_key] = {
                    'status': layer_output.get('status'),
                    'confidence': layer_output.get(f'layer{layer}_confidence', 0.0)
                }
        
        # Add this pass summary to the history
        simulation_data.setdefault('history', []).append(pass_summary)
    
    def _check_termination_conditions(self, simulation_data: Dict[str, Any]) -> bool:
        """
        Check if any termination conditions are met.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            bool: True if should terminate, False if should continue
        """
        current_confidence = simulation_data.get('current_confidence', 0.0)
        target_confidence = simulation_data.get('target_confidence', self.target_confidence)
        status = simulation_data.get('status', 'in_progress')
        
        # Condition 1: Target confidence reached
        if current_confidence >= target_confidence:
            simulation_data['status'] = 'completed_target_confidence'
            logging.info(f"[{datetime.now()}] AO: Terminating - Target confidence reached: {current_confidence:.3f} >= {target_confidence:.3f}")
            return True
        
        # Condition 2: Error status set by a layer
        if status != 'in_progress':
            logging.info(f"[{datetime.now()}] AO: Terminating - Status changed to: {status}")
            return True
        
        # Condition 3: Maximum passes reached
        if simulation_data['current_pass'] >= self.max_passes:
            simulation_data['status'] = 'completed_max_passes'
            logging.info(f"[{datetime.now()}] AO: Terminating - Maximum passes reached: {simulation_data['current_pass']} >= {self.max_passes}")
            return True
        
        # Continue processing if no termination conditions are met
        return False
    
    def _compile_final_answer(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile the final answer package.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Final answer package
        """
        session_id = simulation_data["session_id"]
        final_confidence = simulation_data.get('current_confidence', 0.0)
        status = simulation_data.get('status', 'unknown')
        
        # Get the refined answer text from the last pass
        refined_answer_text = simulation_data.get('refined_answer_text_in_progress', '')
        
        # If no refined answer text is available, create a basic one
        if not refined_answer_text:
            refined_answer_text = f"# Response to Query\n\nQuery: {simulation_data['original_query']}\n\n"
            
            if status == 'error':
                refined_answer_text += f"I encountered an error while processing your query: {simulation_data.get('error_message', 'Unknown error')}"
            else:
                refined_answer_text += "I'm unable to provide a complete answer at this time."
        
        # Create the final answer package
        final_answer = {
            'session_id': session_id,
            'query': simulation_data['original_query'],
            'answer_text': refined_answer_text,
            'confidence': final_confidence,
            'status': status,
            'passes_executed': simulation_data['current_pass'],
            'processing_metadata': {
                'target_confidence': simulation_data.get('target_confidence', self.target_confidence),
                'max_passes': self.max_passes,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Add error message if status is error
        if status == 'error':
            final_answer['error'] = simulation_data.get('error_message', 'Unknown error')
        
        # Log the final answer
        self.smm.add_memory_entry(
            session_id=session_id,
            pass_num=simulation_data['current_pass'],
            layer_num=0,
            entry_type='final_compiled_answer',
            content=final_answer,
            confidence=final_confidence
        )
        
        logging.info(f"[{datetime.now()}] AO: Final answer compiled for session {session_id[:8]}... with confidence {final_confidence:.3f}")
        
        return final_answer
