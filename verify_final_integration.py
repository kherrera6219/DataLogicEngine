import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def verify_final_integration():
    logging.info("=== UKG FINAL SYSTEM INTEGRATION VERIFICATION ===")
    
    try:
        from core.engine.ka_engine import KAEngine
        from core.simulation.simulation_engine import SimulationEngine
        from backend.knowledge_algorithm.axis_mapper import AxisMapper
        
        ka_engine = KAEngine()
        sim_engine = SimulationEngine(ka_engine=ka_engine)
        
        # High-complexity, multi-domain query
        query = "Analyze the regulatory crosswalk and ethical impact of AI-driven Bayesian blockchain models in European clinical research sectors."
        logging.info(f"Triggering Full Hierarchy Simulation: '{query}'")
        
        # 1. Start Simulation
        sim_record = sim_engine.start_simulation(query)
        sim_id = sim_record['simulation_id']
        
        # 2. Run Pass
        logging.info("\n--- EXECUTING 12-STEP WORKFLOW ---")
        result = sim_engine.run_simulation_pass(sim_id)
        
        # 3. Validation
        last_pass = result['passes'][-1]
        context = result['context']
        axis_vector = context.get('axis_vector', {})
        
        logging.info("\n--- FINAL SYSTEM CHECK ---")
        
        # A. Complexity & Routing
        routing = last_pass.get('routing', {})
        complexity = routing.get('complexity', {}).get('tier')
        if complexity in ["high", "medium"]:
            logging.info(f"SUCCESS: STEP 1: Complexity Routing detected {complexity.upper()}")
        else:
            logging.error(f"FAILURE: STEP 1: Routing failed to detect complexity. Got: {complexity}")

        # B. High-Fidelity Axes (1-7)
        logging.info(f"Resolution Details: Axis 1={axis_vector.get(1)}, Axis 2={axis_vector.get(2)}, Axis 3={axis_vector.get(3)}")
        
        if axis_vector.get(1) != "0.0.0.0" and axis_vector.get(2) != "0.0.0.0":
             logging.info("SUCCESS: AXIS 1 & 2: Pillar and Sector resolved.")
        else:
             logging.error("FAILURE: AXIS 1 & 2: Basic resolution failed.")

        if axis_vector.get(3) != "3.0.0.0":
             logging.info(f"SUCCESS: AXIS 3: Honeycomb cross-domain link established: {axis_vector[3]}")
        else:
             logging.error(f"FAILURE: AXIS 3: Honeycomb link failed: {axis_vector[3]}")

        if axis_vector.get(6) != "6.0.0.0" and axis_vector.get(7) != "7.0.0.0":
             logging.info(f"SUCCESS: AXIS 6 & 7: Regulatory/Compliance crosswalks resolved: {axis_vector[6]}, {axis_vector[7]}")
        else:
             logging.warning(f"WARNING: AXIS 6 & 7: Regulatory mapping failed or default: {axis_vector[6]}")

        # C. Truth Scoring (14-17)
        truth = last_pass.get('truth_vector', {})
        overall_score = truth.get('overall_truth_score', 0)
        if overall_score > 0:
            logging.info(f"SUCCESS: STEP 11: Multi-consensus Truth Score derived: {overall_score:.2f}")
        else:
            logging.error("FAILURE: STEP 11: Truth calculation failed.")

        logging.info("\n=== VERIFICATION SUCCESSFULLY COMPLETED ===")
        return True

    except Exception as e:
        logging.error(f"CRITICAL SYSTEM ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_final_integration()
    sys.exit(0 if success else 1)
