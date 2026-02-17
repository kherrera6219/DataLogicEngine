import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def verify_phase2_full_flow():
    logging.info("=== UKG Phase 2 Full Flow Verification ===")
    
    try:
        from core.system.system_initializer import SystemInitializer
        
        # 1. Initialize System
        logging.info("\n1. Initializing UKG System...")
        initializer = SystemInitializer()
        components = initializer.get_components()
        sim_engine = components['simulation_engine']
        ka_engine = components['ka_engine']
        
        logging.info(f"System initialized. KA Engine has {len(ka_engine.list_algorithms())} KAs.")
        
        # 2. Start Simulation
        query = "Regulatory compliance in the financial sector for blockchain systems."
        logging.info(f"\n2. Starting Simulation for Query: '{query}'")
        
        # Create a simulation
        sim_params = {
            'max_passes': 1,
            'personas': {
                'knowledge': {'enabled': True, 'components': ['persona']},
                'sector': {'enabled': True, 'components': ['persona']}
            }
        }
        
        sim_record = sim_engine.start_simulation(query, simulation_params=sim_params)
        sim_id = sim_record['simulation_id']
        logging.info(f"Simulation created: {sim_id}")
        
        # 3. Run Simulation Pass
        logging.info("\n3. Running Simulation Pass 1 (Includes AxisMapper and TruthEngine)...")
        updated_sim = sim_engine.run_simulation_pass(sim_id)
        
        # 4. Verify Axis Mapping
        context = updated_sim.get('context', {})
        axis_vector = context.get('axis_vector', {})
        logging.info("\n4. Verifying Axis Mapping...")
        logging.info(f"Resolved Axis Vector: {axis_vector}")
        
        if axis_vector.get(1) == '1.49.0.0' and axis_vector.get(2) == '2.10.4.1':
            logging.info("SUCCESS: Axis 1 (Pillars) and Axis 2 (Sectors) correctly resolved.")
        else:
            logging.warning("PARTIAL: Axis 1 or 2 resolution mismatch (Expected 1.49.0.0 and 2.10.4.1).")
            
        # 5. Verify Persona Execution (KA-012 / PERSONA)
        logging.info("\n5. Verifying Persona Execution...")
        pass_results = updated_sim.get('passes', [])[0]
        per_res = pass_results.get('persona_results', {})
        
        persona_found = False
        for p_id, res in per_res.items():
            # Check top level or in components
            if 'persona_map' in res.get('response', {}):
                persona_found = True
                logging.info(f"Detected Persona Result for {p_id} (top-level)")
            else:
                for comp_id, comp_res in res.get('components', {}).items():
                    if 'persona_map' in comp_res.get('response', {}):
                        persona_found = True
                        logging.info(f"Detected Persona Result for {p_id}/{comp_id}")
                        break
        
        if persona_found:
            logging.info("SUCCESS: PERSONA (KA-012) class executed correctly.")
        else:
            logging.warning("FAILURE: PERSONA (KA-012) results not found in simulation record.")

        # 6. Verify TruthEngine Integration
        logging.info("\n6. Verifying TruthEngine Integration...")
        truth_vector = pass_results.get('truth_vector')
        validation = pass_results.get('validation')
        
        if truth_vector and 14 in truth_vector:
            logging.info(f"Truth Vector detected: {truth_vector}")
            logging.info(f"Validation Status: {validation}")
            if axis_vector.get(14):
                logging.info(f"Truth Axis 14 Coordinate: {axis_vector[14]}")
                logging.info("SUCCESS: TruthEngine integrated into Simulation Engine.")
            else:
                logging.warning("FAILURE: Truth Axis coordinates not found in Axis Vector.")
        else:
            logging.warning("FAILURE: TruthEngine scores not found in pass record.")

        logging.info("\n=== Phase 2 Integration Verification Complete ===")
        
    except Exception as e:
        logging.error(f"\nFATAL ERROR during verification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_phase2_full_flow()
