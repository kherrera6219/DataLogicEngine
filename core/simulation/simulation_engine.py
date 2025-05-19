import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import uuid
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.ukg_db import UkgDatabaseManager

class SimulationEngine:
    """
    The SimulationEngine handles the execution of the simulation process across
    all layers of the UKG system. It coordinates the processing of input data through
    various knowledge algorithms and simulations to generate high-confidence responses.
    """
    
    def __init__(self, config, graph_manager, memory_manager, ka_loader):
        """
        Initialize the SimulationEngine.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager: Reference to the GraphManager
            memory_manager: Reference to the StructuredMemoryManager
            ka_loader: Reference to the KALoader
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.ka_loader = ka_loader
        self.db_manager = UkgDatabaseManager()
        
        # Get simulation configuration
        self.layer_confidence_thresholds = self.config.get('layer_confidence_thresholds', {
            1: 0.7,  # Layer 1: Retrieval
            2: 0.75, # Layer 2: Comprehension
            3: 0.8,  # Layer 3: Reasoning
            4: 0.85, # Layer 4: Evaluation
            5: 0.9,  # Layer 5: Reconsideration
            6: 0.92, # Layer 6: Verification
            7: 0.95, # Layer 7: Application
            8: 0.97, # Layer 8: Synthesis
            9: 0.99  # Layer 9: Integration
        })
        
        # Layer execution timeouts (in seconds)
        self.layer_timeouts = self.config.get('layer_timeouts', {
            1: 60,   # Layer 1: Retrieval
            2: 60,   # Layer 2: Comprehension
            3: 120,  # Layer 3: Reasoning
            4: 180,  # Layer 4: Evaluation
            5: 180,  # Layer 5: Reconsideration
            6: 240,  # Layer 6: Verification
            7: 180,  # Layer 7: Application
            8: 300,  # Layer 8: Synthesis
            9: 300   # Layer 9: Integration
        })
        
        logging.info(f"[{datetime.now()}] SimulationEngine initialized")
    
    def run_layers_1_3(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run simulation Layers 1-3 (Retrieval, Comprehension, Reasoning).
        These layers are always run for every pass.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        
        logging.info(f"[{datetime.now()}] SimulationEngine: Running Layers 1-3 for session {session_id[:8]}, pass {pass_num}")
        
        # Run Layer 1: Information Retrieval
        simulation_data = self.run_layer_1(simulation_data)
        
        # If Layer 1 failed or didn't provide enough confidence, return early
        if simulation_data.get('status', 'in_progress') != 'in_progress':
            return simulation_data
            
        # Run Layer 2: Comprehension & Context Building
        simulation_data = self.run_layer_2(simulation_data)
        
        # If Layer 2 failed or didn't provide enough confidence, return early
        if simulation_data.get('status', 'in_progress') != 'in_progress':
            return simulation_data
            
        # Run Layer 3: Reasoning & Analysis
        simulation_data = self.run_layer_3(simulation_data)
        
        return simulation_data
    
    def run_layers_up_to(self, simulation_data: Dict[str, Any], max_layer: int) -> Dict[str, Any]:
        """
        Run simulation layers up to the specified max layer.
        This is typically used for higher layers (4-9) after the gatekeeper
        decides more processing is needed.
        
        Args:
            simulation_data (dict): Current simulation data
            max_layer (int): The highest layer to run (4-9)
            
        Returns:
            dict: Updated simulation data
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        
        logging.info(f"[{datetime.now()}] SimulationEngine: Running Layers 4-{max_layer} for session {session_id[:8]}, pass {pass_num}")
        
        # Run Layers 4 through max_layer
        for layer_num in range(4, max_layer + 1):
            # Check if we should continue processing
            if simulation_data.get('status', 'in_progress') != 'in_progress':
                break
                
            # Run the current layer
            method_name = f"run_layer_{layer_num}"
            if hasattr(self, method_name) and callable(getattr(self, method_name)):
                layer_method = getattr(self, method_name)
                simulation_data = layer_method(simulation_data)
            else:
                logging.warning(f"[{datetime.now()}] Layer {layer_num} method not implemented")
        
        return simulation_data
    
    def run_layer_1(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 1: Information Retrieval
        This layer focuses on retrieving relevant information from the UKG
        based on the query.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data with Layer 1 output
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        original_query = simulation_data["original_query"]
        active_location_uids = simulation_data.get("active_location_context_uids", [])
        
        logging.info(f"[{datetime.now()}] SE: Running Layer 1 for session {session_id[:8]}, pass {pass_num}")
        
        try:
            # Record the layer start in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1,
                entry_type='layer_start',
                content={
                    'layer_name': 'Information Retrieval',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Execute KA03: Query Expansion
            ka03_input = {
                'query_text': original_query,
                'pass_num': pass_num
            }
            
            ka03_result = self.ka_loader.execute_ka(
                ka_id=3,
                input_data=ka03_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1
            )
            
            # Execute KA04: Node Retrieval
            expanded_query = original_query
            if ka03_result.get('status') == 'success':
                expanded_query = ka03_result.get('expanded_query', original_query)
                
            ka04_input = {
                'original_query': original_query,
                'expanded_query': expanded_query,
                'pass_num': pass_num,
                'active_location_uids': active_location_uids  # Include location context
            }
            
            ka04_result = self.ka_loader.execute_ka(
                ka_id=4,
                input_data=ka04_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1
            )
            
            # Process retrieved nodes and organize by relevance
            relevant_nodes = []
            if ka04_result.get('status') == 'success':
                # If location context active, filter nodes
                if active_location_uids:
                    retrieved_nodes = ka04_result.get('retrieved_nodes', [])
                    # Apply location-based filtering
                    from core.simulation.location_context_engine import LocationContextEngine
                    lce = LocationContextEngine(self.config, self.gm, None)
                    relevant_nodes = lce.filter_nodes_by_location_context(
                        nodes_data=retrieved_nodes,
                        active_location_uids=active_location_uids
                    )
                    
                    # Add location context to memory
                    self.smm.add_memory_entry(
                        session_id=session_id,
                        pass_num=pass_num,
                        layer_num=1,
                        entry_type='location_filter_applied',
                        content={
                            'active_locations': active_location_uids,
                            'original_node_count': len(retrieved_nodes),
                            'filtered_node_count': len(relevant_nodes)
                        }
                    )
                else:
                    relevant_nodes = ka04_result.get('retrieved_nodes', [])
            
            # Prepare Layer 1 output
            confidence = ka04_result.get('confidence', 0.0)
            layer1_output = {
                'status': 'success' if confidence >= self.layer_confidence_thresholds.get(1, 0.7) else 'insufficient_confidence',
                'expanded_query': expanded_query,
                'relevant_nodes': relevant_nodes,
                'node_count': len(relevant_nodes),
                'layer1_confidence': confidence,
                'ka_executions': [
                    {'ka_id': 3, 'status': ka03_result.get('status')},
                    {'ka_id': 4, 'status': ka04_result.get('status')}
                ]
            }
            
            # Record the layer completion in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1,
                entry_type='layer_complete',
                content={
                    'layer_name': 'Information Retrieval',
                    'status': layer1_output['status'],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=confidence
            )
            
            # Update simulation data
            simulation_data['layer1_output'] = layer1_output
            simulation_data['current_confidence'] = confidence
            
            # If confidence is too low, update status
            if layer1_output['status'] == 'insufficient_confidence':
                simulation_data['status'] = 'insufficient_information'
                logging.warning(f"[{datetime.now()}] SE: Layer 1 confidence ({confidence:.3f}) below threshold ({self.layer_confidence_thresholds.get(1, 0.7):.3f})")
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error in Layer 1: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            
            # Record the error in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1,
                entry_type='layer_error',
                content={
                    'layer_name': 'Information Retrieval',
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            # Update simulation data
            simulation_data['layer1_output'] = {
                'status': 'error',
                'error': error_msg,
                'layer1_confidence': 0.0
            }
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            return simulation_data
    
    def run_layer_2(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 2: Comprehension & Context Building
        This layer focuses on building context and understanding
        the retrieved information.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data with Layer 2 output
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        original_query = simulation_data["original_query"]
        layer1_output = simulation_data.get("layer1_output", {})
        
        logging.info(f"[{datetime.now()}] SE: Running Layer 2 for session {session_id[:8]}, pass {pass_num}")
        
        try:
            # Record the layer start in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type='layer_start',
                content={
                    'layer_name': 'Comprehension & Context Building',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Check if Layer 1 was successful
            if layer1_output.get('status') != 'success':
                raise ValueError("Layer 1 must be successful to run Layer 2")
            
            # Get relevant nodes from Layer 1
            relevant_nodes = layer1_output.get('relevant_nodes', [])
            expanded_query = layer1_output.get('expanded_query', original_query)
            
            # Execute KA05: Context Builder
            ka05_input = {
                'original_query': original_query,
                'expanded_query': expanded_query,
                'relevant_nodes': relevant_nodes,
                'pass_num': pass_num
            }
            
            ka05_result = self.ka_loader.execute_ka(
                ka_id=5,
                input_data=ka05_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2
            )
            
            # Execute KA06: Query Understanding
            ka06_input = {
                'original_query': original_query,
                'expanded_query': expanded_query,
                'context': ka05_result.get('context', {}),
                'pass_num': pass_num
            }
            
            ka06_result = self.ka_loader.execute_ka(
                ka_id=6,
                input_data=ka06_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2
            )
            
            # Prepare Layer 2 output
            confidence = (ka05_result.get('confidence', 0.0) + ka06_result.get('confidence', 0.0)) / 2.0
            layer2_output = {
                'status': 'success' if confidence >= self.layer_confidence_thresholds.get(2, 0.75) else 'insufficient_confidence',
                'context': ka05_result.get('context', {}),
                'query_understanding': ka06_result.get('understanding', {}),
                'identified_intents': ka06_result.get('intents', []),
                'layer2_confidence': confidence,
                'ka_executions': [
                    {'ka_id': 5, 'status': ka05_result.get('status')},
                    {'ka_id': 6, 'status': ka06_result.get('status')}
                ]
            }
            
            # Record the layer completion in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type='layer_complete',
                content={
                    'layer_name': 'Comprehension & Context Building',
                    'status': layer2_output['status'],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=confidence
            )
            
            # Update simulation data
            simulation_data['layer2_output'] = layer2_output
            simulation_data['current_confidence'] = confidence
            
            # If confidence is too low, update status
            if layer2_output['status'] == 'insufficient_confidence':
                simulation_data['status'] = 'insufficient_understanding'
                logging.warning(f"[{datetime.now()}] SE: Layer 2 confidence ({confidence:.3f}) below threshold ({self.layer_confidence_thresholds.get(2, 0.75):.3f})")
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error in Layer 2: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            
            # Record the error in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type='layer_error',
                content={
                    'layer_name': 'Comprehension & Context Building',
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            # Update simulation data
            simulation_data['layer2_output'] = {
                'status': 'error',
                'error': error_msg,
                'layer2_confidence': 0.0
            }
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            return simulation_data
    
    def run_layer_3(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 3: Reasoning & Analysis
        This layer focuses on reasoning and analyzing the information
        to generate initial answers.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data with Layer 3 output
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        original_query = simulation_data["original_query"]
        layer1_output = simulation_data.get("layer1_output", {})
        layer2_output = simulation_data.get("layer2_output", {})
        active_location_uids = simulation_data.get("active_location_context_uids", [])
        applicable_reg_uids = simulation_data.get("applicable_regulatory_framework_uids", [])
        
        logging.info(f"[{datetime.now()}] SE: Running Layer 3 for session {session_id[:8]}, pass {pass_num}")
        
        try:
            # Record the layer start in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=3,
                entry_type='layer_start',
                content={
                    'layer_name': 'Reasoning & Analysis',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Check if Layer 2 was successful
            if layer2_output.get('status') != 'success':
                raise ValueError("Layer 2 must be successful to run Layer 3")
            
            # Get data from previous layers
            relevant_nodes = layer1_output.get('relevant_nodes', [])
            context = layer2_output.get('context', {})
            query_understanding = layer2_output.get('query_understanding', {})
            
            # Execute KA07: Reasoning Algorithm
            ka07_input = {
                'original_query': original_query,
                'relevant_nodes': relevant_nodes,
                'context': context,
                'query_understanding': query_understanding,
                'pass_num': pass_num,
                'active_location_uids': active_location_uids,
                'applicable_reg_uids': applicable_reg_uids
            }
            
            ka07_result = self.ka_loader.execute_ka(
                ka_id=7,
                input_data=ka07_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=3
            )
            
            # Execute KA08: Initial Answer Generation
            ka08_input = {
                'original_query': original_query,
                'reasoning_output': ka07_result.get('reasoning_output', {}),
                'context': context,
                'relevant_nodes': relevant_nodes,
                'pass_num': pass_num,
                'active_location_uids': active_location_uids,
                'applicable_reg_uids': applicable_reg_uids
            }
            
            ka08_result = self.ka_loader.execute_ka(
                ka_id=8,
                input_data=ka08_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=3
            )
            
            # Prepare Layer 3 output
            confidence = (ka07_result.get('confidence', 0.0) + ka08_result.get('confidence', 0.0)) / 2.0
            layer3_output = {
                'status': 'success' if confidence >= self.layer_confidence_thresholds.get(3, 0.8) else 'insufficient_confidence',
                'reasoning_output': ka07_result.get('reasoning_output', {}),
                'initial_answer': ka08_result.get('answer_text', ''),
                'evidence_nodes': ka08_result.get('evidence_nodes', []),
                'layer3_confidence': confidence,
                'ka_executions': [
                    {'ka_id': 7, 'status': ka07_result.get('status')},
                    {'ka_id': 8, 'status': ka08_result.get('status')}
                ]
            }
            
            # Update in-progress answer text
            simulation_data['refined_answer_text_in_progress'] = layer3_output['initial_answer']
            
            # Record the layer completion in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=3,
                entry_type='layer_complete',
                content={
                    'layer_name': 'Reasoning & Analysis',
                    'status': layer3_output['status'],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=confidence
            )
            
            # Update simulation data
            simulation_data['layer3_output'] = layer3_output
            simulation_data['current_confidence'] = confidence
            
            # If confidence is too low, update status
            if layer3_output['status'] == 'insufficient_confidence':
                simulation_data['status'] = 'insufficient_reasoning'
                logging.warning(f"[{datetime.now()}] SE: Layer 3 confidence ({confidence:.3f}) below threshold ({self.layer_confidence_thresholds.get(3, 0.8):.3f})")
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error in Layer 3: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            
            # Record the error in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=3,
                entry_type='layer_error',
                content={
                    'layer_name': 'Reasoning & Analysis',
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            # Update simulation data
            simulation_data['layer3_output'] = {
                'status': 'error',
                'error': error_msg,
                'layer3_confidence': 0.0
            }
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            return simulation_data
    
    def run_layer_4(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 4: Evaluation & Assessment
        This layer focuses on evaluating the initial answer and
        assessing its quality.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data with Layer 4 output
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        original_query = simulation_data["original_query"]
        layer3_output = simulation_data.get("layer3_output", {})
        active_location_uids = simulation_data.get("active_location_context_uids", [])
        
        logging.info(f"[{datetime.now()}] SE: Running Layer 4 for session {session_id[:8]}, pass {pass_num}")
        
        try:
            # Record the layer start in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=4,
                entry_type='layer_start',
                content={
                    'layer_name': 'Evaluation & Assessment',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Check if Layer 3 was successful
            if layer3_output.get('status') != 'success':
                raise ValueError("Layer 3 must be successful to run Layer 4")
            
            # Get data from previous layers
            initial_answer = layer3_output.get('initial_answer', '')
            reasoning_output = layer3_output.get('reasoning_output', {})
            evidence_nodes = layer3_output.get('evidence_nodes', [])
            
            # Execute KA09: Answer Evaluation
            ka09_input = {
                'original_query': original_query,
                'initial_answer': initial_answer,
                'reasoning_output': reasoning_output,
                'evidence_nodes': evidence_nodes,
                'pass_num': pass_num,
                'active_location_uids': active_location_uids
            }
            
            ka09_result = self.ka_loader.execute_ka(
                ka_id=9,
                input_data=ka09_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=4
            )
            
            # Prepare Layer 4 output
            confidence = ka09_result.get('confidence', 0.0)
            layer4_output = {
                'status': 'success' if confidence >= self.layer_confidence_thresholds.get(4, 0.85) else 'insufficient_confidence',
                'evaluation': ka09_result.get('evaluation', {}),
                'identified_gaps': ka09_result.get('identified_gaps', []),
                'quality_score': ka09_result.get('quality_score', 0.0),
                'layer4_confidence': confidence,
                'ka_executions': [
                    {'ka_id': 9, 'status': ka09_result.get('status')}
                ]
            }
            
            # Record the layer completion in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=4,
                entry_type='layer_complete',
                content={
                    'layer_name': 'Evaluation & Assessment',
                    'status': layer4_output['status'],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=confidence
            )
            
            # Update simulation data
            simulation_data['layer4_output'] = layer4_output
            simulation_data['current_confidence'] = (simulation_data['current_confidence'] + confidence) / 2.0
            
            # If confidence is too low, update status
            if layer4_output['status'] == 'insufficient_confidence':
                simulation_data['status'] = 'insufficient_evaluation'
                logging.warning(f"[{datetime.now()}] SE: Layer 4 confidence ({confidence:.3f}) below threshold ({self.layer_confidence_thresholds.get(4, 0.85):.3f})")
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error in Layer 4: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            
            # Record the error in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=4,
                entry_type='layer_error',
                content={
                    'layer_name': 'Evaluation & Assessment',
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            # Update simulation data
            simulation_data['layer4_output'] = {
                'status': 'error',
                'error': error_msg,
                'layer4_confidence': 0.0
            }
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            return simulation_data
    
    def run_layer_5(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 5: Reconsideration & Refinement
        This layer focuses on reconsidering the initial answer and
        refining it based on evaluation.
        
        Args:
            simulation_data (dict): Current simulation data
            
        Returns:
            dict: Updated simulation data with Layer 5 output
        """
        session_id = simulation_data["session_id"]
        pass_num = simulation_data["current_pass"]
        original_query = simulation_data["original_query"]
        layer3_output = simulation_data.get("layer3_output", {})
        layer4_output = simulation_data.get("layer4_output", {})
        
        logging.info(f"[{datetime.now()}] SE: Running Layer 5 for session {session_id[:8]}, pass {pass_num}")
        
        try:
            # Record the layer start in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=5,
                entry_type='layer_start',
                content={
                    'layer_name': 'Reconsideration & Refinement',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Check if Layer 4 was successful
            if layer4_output.get('status') != 'success':
                raise ValueError("Layer 4 must be successful to run Layer 5")
            
            # Get data from previous layers
            initial_answer = layer3_output.get('initial_answer', '')
            evaluation = layer4_output.get('evaluation', {})
            identified_gaps = layer4_output.get('identified_gaps', [])
            
            # Execute KA10: Answer Refinement
            ka10_input = {
                'original_query': original_query,
                'initial_answer': initial_answer,
                'evaluation': evaluation,
                'identified_gaps': identified_gaps,
                'pass_num': pass_num
            }
            
            ka10_result = self.ka_loader.execute_ka(
                ka_id=10,
                input_data=ka10_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=5
            )
            
            # Prepare Layer 5 output
            confidence = ka10_result.get('confidence', 0.0)
            layer5_output = {
                'status': 'success' if confidence >= self.layer_confidence_thresholds.get(5, 0.9) else 'insufficient_confidence',
                'refined_answer': ka10_result.get('refined_answer', initial_answer),
                'refinement_actions': ka10_result.get('refinement_actions', []),
                'layer5_confidence': confidence,
                'ka_executions': [
                    {'ka_id': 10, 'status': ka10_result.get('status')}
                ]
            }
            
            # Update in-progress answer text
            simulation_data['refined_answer_text_in_progress'] = layer5_output['refined_answer']
            
            # Record the layer completion in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=5,
                entry_type='layer_complete',
                content={
                    'layer_name': 'Reconsideration & Refinement',
                    'status': layer5_output['status'],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=confidence
            )
            
            # Update simulation data
            simulation_data['layer5_output'] = layer5_output
            simulation_data['current_confidence'] = (simulation_data['current_confidence'] + confidence) / 2.0
            
            # If confidence is too low, update status
            if layer5_output['status'] == 'insufficient_confidence':
                simulation_data['status'] = 'insufficient_refinement'
                logging.warning(f"[{datetime.now()}] SE: Layer 5 confidence ({confidence:.3f}) below threshold ({self.layer_confidence_thresholds.get(5, 0.9):.3f})")
            
            return simulation_data
            
        except Exception as e:
            error_msg = f"Error in Layer 5: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            
            # Record the error in memory
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=5,
                entry_type='layer_error',
                content={
                    'layer_name': 'Reconsideration & Refinement',
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.0
            )
            
            # Update simulation data
            simulation_data['layer5_output'] = {
                'status': 'error',
                'error': error_msg,
                'layer5_confidence': 0.0
            }
            simulation_data['status'] = 'error'
            simulation_data['error_message'] = error_msg
            
            return simulation_data
    
    # Additional layers 6-9 can be implemented following the same pattern