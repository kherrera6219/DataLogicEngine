import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class SimulationEngine:
    """
    The SimulationEngine is the core component that runs simulations across the layers
    of the UKG system. It manages the flow of information between layers and coordinates
    the execution of various sub-engines (QueryPersonaEngine, RefinementOrchestrator, etc.).
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager, ka_loader):
        """
        Initialize the SimulationEngine.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager (GraphManager): Reference to the GraphManager
            memory_manager (StructuredMemoryManager): Reference to the StructuredMemoryManager
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
            ka_loader (KALoader): Reference to the KALoader
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.ka_loader = ka_loader
        
        # Import here to avoid circular imports
        from core.simulation.query_persona_engine import QueryPersonaEngine
        from core.simulation.refinement_orchestrator import RefinementOrchestrator
        from core.simulation.location_context_engine import LocationContextEngine
        
        # Initialize sub-engines
        self.query_persona_engine = QueryPersonaEngine(
            config=config,
            graph_manager=graph_manager,
            memory_manager=memory_manager,
            united_system_manager=united_system_manager,
            ka_loader=ka_loader
        )
        
        self.refinement_orchestrator = RefinementOrchestrator(
            config=config,
            graph_manager=graph_manager,
            memory_manager=memory_manager,
            united_system_manager=united_system_manager,
            ka_loader=ka_loader
        )
        
        self.location_context_engine = LocationContextEngine(
            config=config,
            graph_manager=graph_manager,
            united_system_manager=united_system_manager
        )
        
        logging.info(f"[{datetime.now()}] SimulationEngine initialized")
    
    def run_layers_1_3(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layers 1-3 of the simulation.
        
        Args:
            simulation_data (dict): Input simulation data
            
        Returns:
            dict: Updated simulation data
        """
        session_id = simulation_data.get('session_id')
        pass_num = simulation_data.get('current_pass', 0)
        query_text = simulation_data.get('original_query', '')
        
        logging.info(f"[{datetime.now()}] SE: Running Layers 1-3 for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        # Process through the three layers
        simulation_data = self._execute_layer1_query_contextualization(simulation_data)
        simulation_data = self._execute_layer2_qpe_and_ro(simulation_data)
        simulation_data = self._execute_layer3_research_agents(simulation_data)
        
        return simulation_data
    
    def run_layers_up_to(self, simulation_data: Dict[str, Any], target_max_layer: int) -> Dict[str, Any]:
        """
        Run layers up to the specified target.
        
        Args:
            simulation_data (dict): Input simulation data
            target_max_layer (int): Maximum layer to run
            
        Returns:
            dict: Updated simulation data
        """
        session_id = simulation_data.get('session_id')
        pass_num = simulation_data.get('current_pass', 0)
        
        logging.info(f"[{datetime.now()}] SE: Running layers up to {target_max_layer} for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        # Always run Layers 1-3 first
        simulation_data = self.run_layers_1_3(simulation_data)
        
        # Then run higher layers as needed
        if target_max_layer >= 4:
            simulation_data = self._execute_layer4_pov_engine(simulation_data)
        
        if target_max_layer >= 5:
            simulation_data = self._execute_layer5_multi_agent(simulation_data)
        
        # Layers 6+ are not implemented in this version
        # These would be implemented in a similar fashion
        
        return simulation_data
    
    def _execute_layer1_query_contextualization(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Layer 1: Query Contextualization.
        
        This layer analyzes the query to determine its context, including relevant
        axis context scores, initial topic mappings, and expansion of knowledge scope.
        
        Args:
            simulation_data (dict): Input simulation data
            
        Returns:
            dict: Updated simulation data with Layer 1 results
        """
        session_id = simulation_data.get('session_id')
        pass_num = simulation_data.get('current_pass', 0)
        query_text = simulation_data.get('original_query', '')
        
        logging.info(f"[{datetime.now()}] SE_L1: Contextualizing query for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        layer1_config = self.config.get('layer1_contextualizer', {})
        
        if not layer1_config.get('enabled', True):
            logging.info(f"[{datetime.now()}] SE_L1: Layer 1 disabled, skipping")
            simulation_data['layer1_output'] = {'status': 'skipped'}
            return simulation_data
        
        try:
            # Step 1: Run KA01 to analyze the query
            ka01_input = {'query_text': query_text}
            ka01_result = self.ka_loader.execute_ka(
                ka_id=1,
                input_data=ka01_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1
            )
            
            if ka01_result.get('status') != 'success':
                logging.warning(f"[{datetime.now()}] SE_L1: KA01 failed: {ka01_result.get('error_message')}")
                simulation_data['layer1_output'] = {
                    'status': 'ka01_failed',
                    'error': ka01_result.get('error_message')
                }
                return simulation_data
            
            # Step 2: Run KA02 to score axes
            ka02_input = {
                'query_text': query_text,
                'ka01_output': ka01_result
            }
            ka02_result = self.ka_loader.execute_ka(
                ka_id=2,
                input_data=ka02_input,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=1
            )
            
            if ka02_result.get('status') != 'success':
                logging.warning(f"[{datetime.now()}] SE_L1: KA02 failed: {ka02_result.get('error_message')}")
                simulation_data['layer1_output'] = {
                    'status': 'ka02_failed',
                    'error': ka02_result.get('error_message'),
                    'ka01_output': ka01_result
                }
                return simulation_data
            
            # Step 3: Determine location context (using LocationContextEngine)
            # This will use KA01's output to identify locations mentioned in the query
            identified_locations = ka01_result.get('findings', {}).get('identified_locations', [])
            location_uids = []
            
            # For each identified location, get its UID
            for loc_info in identified_locations:
                loc_name = loc_info.get('location')
                if loc_name:
                    # Try to find the location in the UKG
                    location_nodes = self.gm.find_location_uids_from_text(loc_name)
                    if location_nodes:
                        location_uids.extend(location_nodes)
            
            # Get the active location context
            if location_uids:
                active_location_context = self.location_context_engine.determine_active_location_context(
                    explicit_location_uids=location_uids
                )
            else:
                active_location_context = self.location_context_engine.determine_active_location_context(
                    query_text=query_text
                )
            
            # Step 4: Create a unique topic UID for this query
            query_topic_uid_pkg = self.usm.create_unified_id(
                entity_label=f"Query: {query_text[:50]}...",
                entity_type="QueryTopic",
                ukg_coords={"OriginalQuery": query_text}
            )
            query_topic_uid = query_topic_uid_pkg["uid_string"]
            
            # Step 5: Prepare axis context scores
            initial_axis_context_scores = {}
            for axis_id, info in ka02_result.get('findings', {}).get('axis_scores', {}).items():
                initial_axis_context_scores[axis_id] = info.get('score', 0.0)
            
            # Calculate layer confidence as average of KA01 and KA02 confidences
            ka01_confidence = ka01_result.get('ka_confidence', 0.5)
            ka02_confidence = ka02_result.get('ka_confidence', 0.5)
            layer1_confidence = (ka01_confidence + ka02_confidence) / 2
            
            # Update simulation data with Layer 1 results
            simulation_data['query_topic_uid'] = query_topic_uid
            simulation_data['initial_axis_context_scores'] = initial_axis_context_scores
            simulation_data['active_location_context'] = active_location_context
            simulation_data['expanded_knowledge_scope_uids'] = []  # To be populated by knowledge expansion
            simulation_data['current_confidence'] = layer1_confidence
            
            # Store Layer 1 output
            simulation_data['layer1_output'] = {
                'status': 'success',
                'ka01_output': ka01_result,
                'ka02_output': ka02_result,
                'active_location_context': active_location_context,
                'query_topic_uid': query_topic_uid,
                'layer1_confidence': layer1_confidence
            }
            
            logging.info(f"[{datetime.now()}] SE_L1: Query contextualization complete. Confidence: {layer1_confidence:.3f}")
            
            return simulation_data
        
        except Exception as e:
            error_msg = f"Error in Layer 1: {str(e)}"
            logging.error(f"[{datetime.now()}] SE_L1: {error_msg}", exc_info=True)
            
            simulation_data['layer1_output'] = {
                'status': 'error',
                'error': error_msg
            }
            
            return simulation_data
    
    def _execute_layer2_qpe_and_ro(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Layer 2: Query Persona Engine and Refinement Orchestrator.
        
        This layer runs the query through multiple personas to get diverse perspectives,
        then refines these perspectives through a 12-step process.
        
        Args:
            simulation_data (dict): Input simulation data with Layer 1 results
            
        Returns:
            dict: Updated simulation data with Layer 2 results
        """
        session_id = simulation_data.get('session_id')
        pass_num = simulation_data.get('current_pass', 0)
        query_text = simulation_data.get('original_query', '')
        query_topic_uid = simulation_data.get('query_topic_uid')
        
        logging.info(f"[{datetime.now()}] SE_L2: Running QPE and RO for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        layer2_config = self.config.get('layer2_qpe_ro', {})
        
        if not layer2_config.get('enabled', True):
            logging.info(f"[{datetime.now()}] SE_L2: Layer 2 disabled, skipping")
            simulation_data['layer2_output'] = {'status': 'skipped'}
            return simulation_data
        
        try:
            # Step 1: Run the Query Persona Engine
            qpe_result = self.query_persona_engine.run(
                query_text=query_text,
                query_topic_uid=query_topic_uid,
                initial_axis_context_scores=simulation_data.get('initial_axis_context_scores', {}),
                active_location_context=simulation_data.get('active_location_context', []),
                session_id=session_id,
                pass_num=pass_num
            )
            
            if qpe_result.get('status') != 'success':
                logging.warning(f"[{datetime.now()}] SE_L2: QPE failed: {qpe_result.get('error')}")
                simulation_data['layer2_output'] = {
                    'status': 'qpe_failed',
                    'error': qpe_result.get('error')
                }
                return simulation_data
            
            # Step 2: Run the Refinement Orchestrator
            ro_result = self.refinement_orchestrator.run(
                qpe_output=qpe_result,
                query_text=query_text,
                query_topic_uid=query_topic_uid,
                initial_axis_context_scores=simulation_data.get('initial_axis_context_scores', {}),
                active_location_context=simulation_data.get('active_location_context', []),
                session_id=session_id,
                pass_num=pass_num
            )
            
            if ro_result.get('status') != 'success':
                logging.warning(f"[{datetime.now()}] SE_L2: RO failed: {ro_result.get('error')}")
                simulation_data['layer2_output'] = {
                    'status': 'ro_failed',
                    'error': ro_result.get('error'),
                    'qpe_output': qpe_result
                }
                return simulation_data
            
            # Update simulation data with Layer 2 results
            layer2_confidence = ro_result.get('final_confidence', 0.7)
            refined_answer_text = ro_result.get('refined_answer_text', '')
            
            simulation_data['current_confidence'] = layer2_confidence
            simulation_data['refined_answer_text_in_progress'] = refined_answer_text
            
            # Store Layer 2 output
            simulation_data['layer2_output'] = {
                'status': 'success',
                'qpe_output': qpe_result,
                'ro_output': ro_result,
                'layer2_confidence': layer2_confidence
            }
            
            logging.info(f"[{datetime.now()}] SE_L2: QPE and RO complete. Confidence: {layer2_confidence:.3f}")
            
            return simulation_data
        
        except Exception as e:
            error_msg = f"Error in Layer 2: {str(e)}"
            logging.error(f"[{datetime.now()}] SE_L2: {error_msg}", exc_info=True)
            
            simulation_data['layer2_output'] = {
                'status': 'error',
                'error': error_msg
            }
            
            return simulation_data
    
    def _execute_layer3_research_agents(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Layer 3: Research Agents.
        
        This layer conducts targeted research to fill knowledge gaps
        identified in Layer 2.
        
        Args:
            simulation_data (dict): Input simulation data with Layer 2 results
            
        Returns:
            dict: Updated simulation data with Layer 3 results
        """
        session_id = simulation_data.get('session_id')
        pass_num = simulation_data.get('current_pass', 0)
        query_topic_uid = simulation_data.get('query_topic_uid')
        
        logging.info(f"[{datetime.now()}] SE_L3: Running Research Agents for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        layer3_config = self.config.get('layer3_research', {})
        
        if not layer3_config.get('enabled', True):
            logging.info(f"[{datetime.now()}] SE_L3: Layer 3 disabled, skipping")
            simulation_data['layer3_output'] = {'status': 'skipped'}
            return simulation_data
        
        # Check if Layer 2 identified any research needs
        if 'layer2_output' not in simulation_data or simulation_data['layer2_output'].get('status') != 'success':
            logging.info(f"[{datetime.now()}] SE_L3: No valid Layer 2 output, skipping Layer 3")
            simulation_data['layer3_output'] = {'status': 'skipped_no_layer2_data'}
            return simulation_data
        
        try:
            # Extract research needs from RO output
            ro_output = simulation_data['layer2_output'].get('ro_output', {})
            research_needs = ro_output.get('research_needs', [])
            
            if not research_needs:
                logging.info(f"[{datetime.now()}] SE_L3: No research needs identified, skipping")
                simulation_data['layer3_output'] = {'status': 'skipped_no_research_needs'}
                return simulation_data
            
            # In a full implementation, this would dispatch specialized research agents
            # For simplicity, we'll just log the research needs and provide a basic mock
            logging.info(f"[{datetime.now()}] SE_L3: Processing {len(research_needs)} research needs")
            
            research_results = []
            overall_research_confidence = 0.0
            
            for i, need in enumerate(research_needs):
                need_id = need.get('id', f"need_{i}")
                need_description = need.get('description', 'Unknown research need')
                need_priority = need.get('priority', 'medium')
                
                # Mock research result (in a real system, this would use specialized KAs or external APIs)
                result = {
                    'need_id': need_id,
                    'need_description': need_description,
                    'status': 'completed',
                    'confidence': 0.75,  # Mock confidence
                    'findings': f"Research findings for {need_description}",
                    'sources': ['UKG Internal', 'Mock Research Source']
                }
                
                research_results.append(result)
                overall_research_confidence += result['confidence']
            
            # Calculate average confidence if there are results
            if research_results:
                overall_research_confidence /= len(research_results)
            
            # Update the answer text with research findings
            refined_answer_text = simulation_data.get('refined_answer_text_in_progress', '')
            if refined_answer_text and research_results:
                research_additions = "\n\nAdditional Research Findings:\n"
                for result in research_results:
                    research_additions += f"- {result['findings']}\n"
                
                refined_answer_text += research_additions
                simulation_data['refined_answer_text_in_progress'] = refined_answer_text
            
            # Update confidence
            layer3_confidence = (simulation_data.get('current_confidence', 0.7) + overall_research_confidence) / 2
            simulation_data['current_confidence'] = layer3_confidence
            
            # Store Layer 3 output
            simulation_data['layer3_output'] = {
                'status': 'success',
                'research_needs_processed': len(research_needs),
                'research_results': research_results,
                'layer3_confidence': layer3_confidence
            }
            
            logging.info(f"[{datetime.now()}] SE_L3: Research complete. Confidence: {layer3_confidence:.3f}")
            
            return simulation_data
        
        except Exception as e:
            error_msg = f"Error in Layer 3: {str(e)}"
            logging.error(f"[{datetime.now()}] SE_L3: {error_msg}", exc_info=True)
            
            simulation_data['layer3_output'] = {
                'status': 'error',
                'error': error_msg
            }
            
            return simulation_data
    
    def _execute_layer4_pov_engine(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Layer 4: Point of View Engine.
        
        This layer explores alternative points of view on the query.
        Not fully implemented in this version.
        
        Args:
            simulation_data (dict): Input simulation data
            
        Returns:
            dict: Updated simulation data
        """
        # This is a placeholder for Layer 4
        logging.info(f"[{datetime.now()}] SE_L4: POV Engine not implemented in this version, skipping")
        simulation_data['layer4_output'] = {'status': 'not_implemented'}
        return simulation_data
    
    def _execute_layer5_multi_agent(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Layer 5: Multi-Agent System.
        
        This layer orchestrates specialized agents for complex tasks.
        Not fully implemented in this version.
        
        Args:
            simulation_data (dict): Input simulation data
            
        Returns:
            dict: Updated simulation data
        """
        # This is a placeholder for Layer 5
        logging.info(f"[{datetime.now()}] SE_L5: Multi-Agent System not implemented in this version, skipping")
        simulation_data['layer5_output'] = {'status': 'not_implemented'}
        return simulation_data
