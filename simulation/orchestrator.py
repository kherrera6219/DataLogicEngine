"""
Universal Knowledge Graph (UKG) System - Simulation Orchestrator

This module provides the orchestration layer that connects all three layers of the
Nested Layered In-Memory Simulation Management System.
"""

import logging
from typing import Dict, Any, Optional

from simulation.layer1_entry import create_simulation_entry_controller
from simulation.layer2_knowledge import create_layer2_simulator
from simulation.layer3_agents import create_layer3_simulator

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    """
    Orchestrates the three-layer simulation system for the Universal Knowledge Graph.
    
    Layer 1: Simulation Entry Layer - Gateway that receives queries and routes them
    Layer 2: Nested Simulated Knowledge Database - Contains the UKG and Quad Persona Engine
    Layer 3: Simulated Research Agent Layer - Delegates to AI agents for deeper analysis
    """
    
    def __init__(self):
        """Initialize the simulation orchestrator."""
        logger.info("Initializing SimulationOrchestrator")
        
        # Create Layer 3 first (bottom-up initialization)
        logger.info("Creating Layer 3 Research Simulator")
        self.layer3 = create_layer3_simulator()
        
        # Create Layer 2 with reference to Layer 3
        logger.info("Creating Layer 2 Knowledge Simulator")
        self.layer2 = create_layer2_simulator(self.layer3)
        
        # Create Layer 1 with reference to Layer 2
        logger.info("Creating Layer 1 Entry Controller")
        self.layer1 = create_simulation_entry_controller(self.layer2)
        
        logger.info("SimulationOrchestrator initialized successfully")
    
    def process_query(self, query_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query through the three-layer simulation system.
        
        Args:
            query_text: The text of the query to process
            context: Optional context information for the query
            
        Returns:
            The processed result
        """
        logger.info(f"Processing query: {query_text[:50]}...")
        
        # Use Layer 1 as the entry point
        result = self.layer1.receive_query(query_text, context)
        
        logger.info(f"Query processing complete, result confidence: {result.get('confidence', 0)}")
        
        return result


def create_simulation_orchestrator() -> SimulationOrchestrator:
    """
    Create and initialize the simulation orchestrator.
    
    Returns:
        A configured SimulationOrchestrator
    """
    return SimulationOrchestrator()