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

def verify_phase4_workflow():
    logging.info("=== UKG Phase 4 Workflow & Batch 1 KA Verification ===")
    
    try:
        # 1. Initialize Components
        logging.info("1. Initializing UKG System...")
        from core.engine.ka_engine import KAEngine
        from core.simulation.simulation_engine import SimulationEngine
        
        ka_engine = KAEngine()
        sim_engine = SimulationEngine(ka_engine=ka_engine)
        
        # 2. Start Simulation with a complex query
        query = "What are the regulatory ethics and compliance requirements for Bayesian quantum blockchain in EU financial sectors?"
        logging.info(f"2. Starting High-Complexity Simulation for: '{query}'")
        
        sim_record = sim_engine.start_simulation(query)
        sim_id = sim_record['simulation_id']
        
        # 3. Run Simulation Pass
        logging.info("3. Running Simulation Pass (Executing 12-step workflow)...")
        sim_result = sim_engine.run_simulation_pass(sim_id)
        
        # 4. Verify Workflow Execution
        last_pass = sim_result['passes'][-1]
        
        # A. Check Complexity Routing (Step 1)
        routing = last_pass.get('routing', {})
        complexity = routing.get('complexity', {}).get('tier')
        pipeline = routing.get('pipeline', [])
        
        if complexity == "high":
            logging.info(f"SUCCESS: KA-113 correctly identified HIGH complexity (Hits: {routing['complexity'].get('hits', 'N/A')}).")
        else:
            logging.error(f"FAILURE: KA-113 failed to detect high complexity. Found: {complexity}")
            
        if "KA-006" in pipeline:
            logging.info("SUCCESS: KA-031 correctly injected Deep Planning (KA-006) into high-complexity pipeline.")
        else:
            logging.error(f"FAILURE: KA-031 did not inject KA-006 for high complexity.")

        # B. Check Axis Resolution (Step 2)
        axis_vector = sim_result['context'].get('axis_vector', {})
        if axis_vector.get(1) != "0.0.0.0" and axis_vector.get(2) != "0.0.0.0":
            logging.info(f"SUCCESS: Axis Mapping (Step 2) resolved Pillar {axis_vector.get(1)} and Sector {axis_vector.get(2)}.")
        else:
            logging.error(f"FAILURE: Step 2 Axis Mapping failed. Vector: {axis_vector}")

        # C. Check Persona Results (Step 3)
        per_res = last_pass.get('persona_results', {})
        if per_res:
            logging.info(f"SUCCESS: Step 3 executed {len(per_res)} expert personas.")
        else:
            logging.error("FAILURE: Step 3 Persona Simulation failed to produce results.")

        # D. Check Truth Validation (Step 11)
        truth_score = last_pass.get('truth_vector', {}).get('overall_truth_score', 0)
        validation = last_pass.get('validation', {}).get('is_valid')
        
        if truth_score > 0:
            logging.info(f"SUCCESS: Step 11 TruthEngine calculated overall score: {truth_score:.2f}")
        else:
            logging.error("FAILURE: Step 11 TruthEngine failed to calculate scores.")

        logging.info("\n=== Phase 4 Integration Verification Complete ===")
        return True

    except Exception as e:
        logging.error(f"CRITICAL FAILURE during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_phase4_workflow()
    sys.exit(0 if success else 1)
