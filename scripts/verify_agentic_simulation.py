import logging
import sys
import os

# Ensure the root directory is in the path
sys.path.append(os.getcwd())

from core.simulation.legacy_simulation_engine import create_simulation_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyAgentic")

def main():
    engine = create_simulation_engine()
    
    query = "How should we implement AI Governance in the UKG Desktop shell?"
    
    logger.info("--- Starting Agentic Simulation ---")
    # Run with agentic mode enabled
    uae = engine.run_simulation(query, escalation_level=3, use_agentic=True)
    
    logger.info("--- Simulation Complete ---")
    logger.info(f"Artifact ID: {uae.artifact_id}")
    logger.info(f"Overall Confidence: {uae.confidence_vector.overall}")
    logger.info(f"Final Output: {uae.payload.get('final_output')}")
    
    # Check analysis steps
    steps = uae.payload.get('analysis_steps', [])
    logger.info(f"Analysis Steps Taken: {len(steps)}")
    for step in steps:
        logger.info(f"  - {step}")

    # Verify metadata
    if uae.metadata.get("agentic_mode"):
        logger.info("SUCCESS: Agentic mode verified in metadata.")
    else:
        logger.error("FAILURE: Agentic mode flag missing in metadata.")

if __name__ == "__main__":
    main()
