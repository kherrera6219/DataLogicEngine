"""
Verification Script: Deep Stack Integration (L1-L10)

This script validates that the Simulation Engine correctly executes the 10-layer stack,
generates Unified Artifact Envelopes (UAE), and registers them in the Trace service.
"""

import os
import sys
import logging
from datetime import datetime, UTC

# Add project root to path
sys.path.append(os.getcwd())

from core.system.united_system_manager import UnitedSystemManager
from simulation.simulation_engine import SimulationEngine
from core.coordinate_system import UnifiedCoordinate

def verify_integration():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VerifyIntegration")
    
    # 1. Initialize System
    logger.info("Initializing United System Manager...")
    usm = UnitedSystemManager()
    
    # 2. Setup Core Services
    # Note: Using registries if available, otherwise default
    axis_registry = "data/registries/axis_registry.json"
    usm.initialize_unified_system(axis_registry if os.path.exists(axis_registry) else None)
    
    # 3. Setup Simulation Engine
    logger.info("Setting up Simulation Engine...")
    sim_engine = SimulationEngine(usm=usm)
    usm.register_component("simulation_engine", sim_engine)
    
    # 4. Execute Simulation Trace
    query = "Analyze the impact of LiDAR sensor failure on Level 4 autonomous vehicle safety regulations."
    logger.info(f"Executing simulation for query: {query}")
    
    # Start at escalation level 5 (Full L1-L10)
    final_envelope = sim_engine.execute_simulation(query, escalation_level=5)
    
    # 5. Validate Output
    logger.info("--- Validation Results ---")
    logger.info(f"Artifact ID: {final_envelope.artifact_id}")
    logger.info(f"Run ID: {final_envelope.run_id}")
    logger.info(f"Confidence: {final_envelope.confidence_vector.overall}")
    logger.info(f"Coordinates: {final_envelope.coord17.to_coordinate_string()}")
    
    # Check Provenance
    logger.info(f"Provenance Entries: {len(final_envelope.provenance)}")
    for entry in final_envelope.provenance:
        logger.info(f"  - {entry.operation} (via {entry.source_id})")
        
    # Check Trace Service
    trace = usm.get_component("trace")
    if trace:
        logger.info(f"Trace Log Size: {len(trace.trace_log)}")
        chain = trace.get_provenance_chain(final_envelope.artifact_id)
        logger.info(f"Backwards Trace Chain Length: {len(chain)}")
        
    # Check Persona Insights
    insights = [k for k in final_envelope.payload.keys() if "persona" in k]
    logger.info(f"Dynamic Persona Insights Found: {insights}")
    
    # Assertion
    assert final_envelope.confidence_vector.overall > 0.8
    assert len(final_envelope.provenance) >= 10
    logger.info("INTEGRATION VERIFIED SUCCESSFUL")

if __name__ == "__main__":
    verify_integration()
