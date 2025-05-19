import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import core components
from core.system.system_initializer import SystemInitializer
from core.system.united_system_manager import UnitedSystemManager
from backend.ukg_db import UkgDatabaseManager

class AppOrchestrator:
    """
    App Orchestrator
    
    This component serves as the main entry point for the UKG system, orchestrating
    high-level operations and providing a unified API for external interactions.
    It coordinates the initialization and operation of all system components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the App Orchestrator.
        
        Args:
            config_path (str, optional): Path to the configuration file
        """
        logging.info(f"[{datetime.now()}] Initializing AppOrchestrator...")
        
        # Initialize database connection
        self.db_manager = self._initialize_database()
        
        # Initialize the core system
        self.system_initializer = SystemInitializer(config_path)
        
        # Get components from system initializer
        components = self.system_initializer.get_components()
        self.usm = components.get('usm')
        self.graph_manager = components.get('gm')
        self.memory_manager = components.get('smm')
        self.ka_engine = components.get('ka_engine')
        self.simulation_engine = components.get('simulation_engine')
        self.location_context_engine = components.get('location_context_engine')
        self.sekre_engine = components.get('sekre_engine')
        
        # Set up component relationships
        if self.graph_manager and self.db_manager:
            self.graph_manager.set_db_manager(self.db_manager)
        
        logging.info(f"[{datetime.now()}] AppOrchestrator initialized and system components connected")
    
    def _initialize_database(self) -> Optional[UkgDatabaseManager]:
        """
        Initialize the database connection.
        
        Returns:
            UkgDatabaseManager: Database manager or None if initialization failed
        """
        try:
            # Check for DATABASE_URL environment variable
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                logging.warning(f"[{datetime.now()}] AO: DATABASE_URL environment variable not found")
                return None
            
            # Create database manager
            db_manager = UkgDatabaseManager(database_url=database_url)
            logging.info(f"[{datetime.now()}] AO: Database connection established")
            
            return db_manager
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error initializing database: {str(e)}")
            return None
    
    def run_simulation(self, query_text: str, location_uids: Optional[List[str]] = None,
                    target_confidence: Optional[float] = None) -> Dict:
        """
        Run a full simulation using the UKG system.
        
        Args:
            query_text: The user's query
            location_uids: Optional list of location UIDs for context
            target_confidence: Optional target confidence threshold
            
        Returns:
            dict: Simulation results
        """
        logging.info(f"[{datetime.now()}] AO: Running simulation for query: {query_text}")
        
        try:
            # Check for required components
            if not self.simulation_engine:
                raise Exception("Simulation Engine not available")
            
            # Start the simulation
            simulation_result = self.simulation_engine.start_simulation(
                user_query=query_text,
                explicit_location_uids=location_uids,
                target_confidence=target_confidence
            )
            
            # Get session ID from result
            session_id = simulation_result.get('session_id')
            
            if not session_id:
                raise Exception("Failed to get session ID from simulation result")
            
            # Wait for simulation to complete
            status = 'running'
            max_wait_iterations = 600  # Avoid infinite loop
            iterations = 0
            
            while status in ('running', 'initializing') and iterations < max_wait_iterations:
                # Get current status
                status_info = self.simulation_engine.get_simulation_status(session_id)
                status = status_info.get('status', 'unknown')
                
                # Break if simulation is complete
                if status not in ('running', 'initializing'):
                    break
                
                # Wait a bit before checking again
                import time
                time.sleep(0.5)
                iterations += 1
            
            # Get final result
            final_result = self.simulation_engine.get_simulation_result(session_id)
            
            if not final_result:
                raise Exception(f"Failed to get final result for session {session_id}")
            
            # Run SEKRE analysis in the background if available
            if self.sekre_engine:
                try:
                    self.sekre_engine.analyze_simulation_results(session_id)
                except Exception as e:
                    logging.error(f"[{datetime.now()}] AO: Error in SEKRE analysis: {str(e)}")
            
            return {
                'session_id': session_id,
                'query': query_text,
                'result': final_result,
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error running simulation: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query_text
            }
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        Get information about a simulation session.
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Session information
        """
        logging.info(f"[{datetime.now()}] AO: Getting session info for {session_id}")
        
        try:
            # Check for required components
            if not self.simulation_engine:
                raise Exception("Simulation Engine not available")
            
            if not self.memory_manager:
                raise Exception("Memory Manager not available")
            
            # Get simulation status
            simulation_status = self.simulation_engine.get_simulation_status(session_id)
            
            # Get session history from memory
            session_history = self.memory_manager.get_session_history(session_id)
            
            # Combine information
            return {
                'session_id': session_id,
                'simulation_status': simulation_status,
                'memory_entries_count': len(session_history.get('raw_memory_entries', [])),
                'user_query': session_history.get('user_query', ''),
                'final_confidence': session_history.get('final_confidence', 0.0),
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error getting session info: {str(e)}")
            return {
                'session_id': session_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_location_context(self, location_uid: Optional[str] = None, 
                           query_text: Optional[str] = None) -> Dict:
        """
        Get location context information.
        
        Args:
            location_uid: Optional specific location UID
            query_text: Optional query text to extract locations from
            
        Returns:
            dict: Location context information
        """
        logging.info(f"[{datetime.now()}] AO: Getting location context")
        
        try:
            # Check for required components
            if not self.location_context_engine:
                raise Exception("Location Context Engine not available")
            
            # If location UID is provided, get info for that location
            if location_uid:
                location_info = self.location_context_engine.get_location_info(location_uid)
                
                if not location_info:
                    raise Exception(f"Location with UID {location_uid} not found")
                
                # Get child locations
                child_locations = self.location_context_engine.get_child_locations(location_uid)
                
                # Get applicable regulations
                regulations = self.location_context_engine.get_applicable_regulations([location_uid])
                
                return {
                    'location': location_info,
                    'child_locations': child_locations,
                    'applicable_regulations': regulations,
                    'status': 'success'
                }
            
            # If query text is provided, determine context from it
            elif query_text:
                # Determine active location context
                location_uids = self.location_context_engine.determine_active_location_context(
                    query_text=query_text
                )
                
                # Get location info for each UID
                locations = []
                for uid in location_uids:
                    loc_info = self.location_context_engine.get_location_info(uid)
                    if loc_info:
                        locations.append(loc_info)
                
                # Get applicable regulations
                regulations = self.location_context_engine.get_applicable_regulations(location_uids)
                
                return {
                    'active_location_uids': location_uids,
                    'locations': locations,
                    'applicable_regulations': regulations,
                    'status': 'success'
                }
            
            # If neither is provided, return an error
            else:
                raise Exception("Either location_uid or query_text must be provided")
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error getting location context: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_system_health(self) -> Dict:
        """
        Get overall system health status.
        
        Returns:
            dict: System health information
        """
        logging.info(f"[{datetime.now()}] AO: Getting system health")
        
        try:
            # Get health info from USM if available
            if self.usm:
                return self.usm.get_system_health()
            
            # Otherwise, provide basic health info
            return {
                'status': 'partial',
                'message': 'United System Manager not available',
                'timestamp': datetime.now().isoformat(),
                'component_status': {
                    'app_orchestrator': 'healthy',
                    'db_manager': 'healthy' if self.db_manager else 'unavailable',
                    'system_initializer': 'healthy' if self.system_initializer else 'unavailable',
                    'usm': 'unavailable',
                    'graph_manager': 'healthy' if self.graph_manager else 'unavailable',
                    'memory_manager': 'healthy' if self.memory_manager else 'unavailable',
                    'ka_engine': 'healthy' if self.ka_engine else 'unavailable',
                    'simulation_engine': 'healthy' if self.simulation_engine else 'unavailable',
                    'location_context_engine': 'healthy' if self.location_context_engine else 'unavailable',
                    'sekre_engine': 'healthy' if self.sekre_engine else 'unavailable'
                }
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error getting system health: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def search_knowledge_graph(self, query: str, node_types: Optional[List[str]] = None,
                             axis_numbers: Optional[List[int]] = None, limit: int = 100) -> Dict:
        """
        Search the knowledge graph.
        
        Args:
            query: Search query
            node_types: Optional list of node types to filter by
            axis_numbers: Optional list of axis numbers to filter by
            limit: Maximum number of results to return
            
        Returns:
            dict: Search results
        """
        logging.info(f"[{datetime.now()}] AO: Searching knowledge graph for: {query}")
        
        try:
            # Check for required components
            if not self.graph_manager:
                raise Exception("Graph Manager not available")
            
            # Search nodes
            nodes = self.graph_manager.search_nodes(query, node_types, axis_numbers, limit)
            
            return {
                'query': query,
                'results_count': len(nodes),
                'nodes': nodes,
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error searching knowledge graph: {str(e)}")
            return {
                'query': query,
                'status': 'error',
                'error': str(e)
            }
    
    def get_improvement_proposals(self, status: Optional[str] = None,
                               proposal_type: Optional[str] = None, limit: int = 100) -> Dict:
        """
        Get improvement proposals generated by the SEKRE engine.
        
        Args:
            status: Optional status filter
            proposal_type: Optional proposal type filter
            limit: Maximum number of proposals to return
            
        Returns:
            dict: Improvement proposals
        """
        logging.info(f"[{datetime.now()}] AO: Getting improvement proposals")
        
        try:
            # Check for required components
            if not self.sekre_engine:
                raise Exception("SEKRE Engine not available")
            
            # Get proposals
            proposals = self.sekre_engine.get_improvement_proposals(status, proposal_type, limit)
            
            return {
                'count': len(proposals),
                'proposals': proposals,
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error getting improvement proposals: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def approve_improvement(self, proposal_id: str) -> Dict:
        """
        Approve and apply an improvement proposal.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            dict: Result of approving the improvement
        """
        logging.info(f"[{datetime.now()}] AO: Approving improvement proposal {proposal_id}")
        
        try:
            # Check for required components
            if not self.sekre_engine:
                raise Exception("SEKRE Engine not available")
            
            # Approve proposal
            result = self.sekre_engine.approve_improvement(proposal_id)
            
            return {
                'proposal_id': proposal_id,
                'result': result,
                'status': 'success' if result.get('status') == 'success' else 'error'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error approving improvement proposal: {str(e)}")
            return {
                'proposal_id': proposal_id,
                'status': 'error',
                'error': str(e)
            }
    
    def reject_improvement(self, proposal_id: str, reason: Optional[str] = None) -> Dict:
        """
        Reject an improvement proposal.
        
        Args:
            proposal_id: Proposal ID
            reason: Optional reason for rejection
            
        Returns:
            dict: Result of rejecting the improvement
        """
        logging.info(f"[{datetime.now()}] AO: Rejecting improvement proposal {proposal_id}")
        
        try:
            # Check for required components
            if not self.sekre_engine:
                raise Exception("SEKRE Engine not available")
            
            # Reject proposal
            result = self.sekre_engine.reject_improvement(proposal_id, reason)
            
            return {
                'proposal_id': proposal_id,
                'result': result,
                'status': 'success' if result.get('status') == 'success' else 'error'
            }
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] AO: Error rejecting improvement proposal: {str(e)}")
            return {
                'proposal_id': proposal_id,
                'status': 'error',
                'error': str(e)
            }