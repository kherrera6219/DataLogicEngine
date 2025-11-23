
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any

class AppOrchestrator:
    """
    AppOrchestrator is the main controller that coordinates all components
    of the UKG/USKD system. It routes user queries through the simulation
    pipeline and manages the execution of the knowledge simulation.
    """
    
    def __init__(self, config):
        """
        Initialize the App Orchestrator.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.ukg_graph_manager = None
        self.uskd_memory_manager = None
        self.united_system_manager = None
        self.simulation_engine = None
        self.ka_loader = None
        self.mcp_manager = None

        self._initialize_systems()
        self._initialize_mcp()
        
        self.logger.info("AppOrchestrator initialized")
    
    def _initialize_systems(self):
        """
        Initialize all subsystems used by the orchestrator.
        """
        try:
            # Import manager classes
            from core.united_system_manager import UnitedSystemManager
            from core.graph_manager import GraphManager
            from core.structured_memory_manager import StructuredMemoryManager
            from core.simulation_engine import SimulationEngine
            from core.knowledge_algorithm.ka_loader import KALoader
            
            # Initialize UnitedSystemManager first (for UID generation)
            self.logger.info("Initializing UnitedSystemManager...")
            self.united_system_manager = UnitedSystemManager(self.config)
            
            # Initialize GraphManager
            self.logger.info("Initializing GraphManager...")
            self.ukg_graph_manager = GraphManager(self.config, self.united_system_manager)
            
            # Initialize StructuredMemoryManager
            self.logger.info("Initializing StructuredMemoryManager...")
            self.uskd_memory_manager = StructuredMemoryManager(self.config)

            # Initialize KALoader
            self.logger.info("Initializing KALoader...")
            self.ka_loader = KALoader(
                self.config,
                self.ukg_graph_manager,
                self.uskd_memory_manager,
                self.united_system_manager
            )

            # Initialize SimulationEngine
            self.logger.info("Initializing SimulationEngine...")
            self.simulation_engine = SimulationEngine(
                self.config,
                self.ukg_graph_manager,
                self.uskd_memory_manager,
                self.united_system_manager,
                self.ka_loader
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing systems: {str(e)}")
            # Continue with the available systems

    def _initialize_mcp(self):
        """
        Initialize the Model Context Protocol (MCP) manager and setup default servers.
        """
        try:
            from core.mcp import MCPManager

            self.logger.info("Initializing MCP Manager...")
            self.mcp_manager = MCPManager(app_orchestrator=self)

            # Setup default MCP servers
            self.logger.info("Setting up default MCP servers...")
            ukg_server = self.mcp_manager.setup_default_servers()

            self.logger.info(f"MCP Manager initialized with {len(self.mcp_manager.servers)} server(s)")

        except Exception as e:
            self.logger.error(f"Error initializing MCP Manager: {str(e)}")
            # MCP is optional, continue without it

    def process_request(self, user_query: str, user_id: Optional[str] = None, 
                      session_id: Optional[str] = None, 
                      simulation_params: Optional[Dict] = None) -> Dict:
        """
        Process a user query through the UKG/USKD simulation pipeline.
        
        Args:
            user_query: The user's natural language query
            user_id: Optional user identifier
            session_id: Optional session identifier (generated if None)
            simulation_params: Optional parameters for simulation control
            
        Returns:
            Dict containing the simulation results
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        self.logger.info(f"Processing request: session_id={session_id}, query='{user_query[:50]}...'")
        
        # Check if critical components are available
        if not self.simulation_engine:
            error_msg = "SimulationEngine not initialized"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "FAILED"}
            
        if not self.ukg_graph_manager:
            error_msg = "GraphManager not initialized"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "FAILED"}
            
        if not self.uskd_memory_manager:
            error_msg = "StructuredMemoryManager not initialized"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "FAILED"}
            
        # Run the simulation with all parameters
        result = self.simulation_engine.run_simulation(
            user_query=user_query, 
            session_id=session_id,
            user_id=user_id,
            simulation_params=simulation_params
        )
        
        # Log the completion
        self.logger.info(f"Request processed: session_id={session_id}, status={result.get('status')}, confidence={result.get('current_confidence', 0):.4f}")
        
        return result
    
    def get_session_memory(self, session_id: str) -> List[Dict]:
        """
        Get memory entries for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of memory entries
        """
        if not self.uskd_memory_manager:
            self.logger.error("StructuredMemoryManager not initialized")
            return []
            
        return self.uskd_memory_manager.get_session_memory(session_id)
    
    def clear_session(self, session_id: str) -> Dict:
        """
        Clear all memory for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with operation result
        """
        if not self.uskd_memory_manager:
            self.logger.error("StructuredMemoryManager not initialized")
            return {"success": False, "error": "Memory manager not initialized"}
            
        count = self.uskd_memory_manager.clear_session_memory(session_id)
        return {"success": True, "cleared_entries": count}
