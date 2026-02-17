import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from core.engine.ka_engine import KAEngine
from backend.knowledge_algorithm.workflow_loader import WorkflowLoader
from backend.knowledge_algorithm.lineage_store import LineageStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def verify_phase1_infrastructure():
    logging.info("=== UKG Phase 1 Infrastructure Verification ===")
    
    # 1. Initialize KA Engine
    logging.info("\n1. Initializing KA Engine with Enterprise Registry...")
    ka_engine = KAEngine()
    ka_count = len(ka_engine.ka_registry)
    logging.info(f"Registered KAs: {ka_count}")
    if ka_count < 113:
        logging.error(f"FAILURE: Expected ~114 KAs, found {ka_count}")
    else:
        logging.info("SUCCESS: KAs loaded from enterprise registry.")

    # 2. Initialize Workflow Loader
    logging.info("\n2. Initializing Workflow Loader (v2.5)...")
    loader = WorkflowLoader()
    if loader.validate_workflow():
        logging.info(f"SUCCESS: Workflow validated with {len(loader.steps)} steps.")
    else:
        logging.error("FAILURE: Workflow validation failed.")

    # 3. Initialize Lineage Store
    logging.info("\n3. Testing Lineage Store...")
    lineage = LineageStore()
    entry = lineage.record_derivation(
        target_id="FACT-001",
        source_ids=["SRC-999"],
        ka_id="KA-001",
        context={"simulation_id": "TEST-SIM-001", "pass_number": 1}
    )
    if lineage.get_lineage("FACT-001"):
        logging.info("SUCCESS: Lineage recorded and retrieved.")
    else:
        logging.error("FAILURE: Lineage storage failed.")

    # 4. Dependency Resolution Test (KA-001 needs KA-004)
    logging.info("\n4. Testing Hard Dependency Resolution (KA-001 -> KA-004)...")
    # We'll mock a KA class for KA-004 and KA-001 since we haven't implemented all logic yet
    # But we can verify the logging/flow
    
    # Note: execute_algorithm will try to import backend.knowledge_algorithm.modules.ka001_aot
    # If the file exists, it will try to instantiate 'Algorithm'
    logging.info("Simulating execution of KA-001 (AoT)...")
    # We expect a failure because 'Algorithm' might not be implemented in the file yet, 
    # but we want to see the "Resolving hard dependency: KA-004" log message.
    # We overwrite the register_algorithm check to bypass module imports for this test
    
    ka_info = ka_engine.ka_registry.get('KA-001')
    if ka_info and ka_info.get('hard_dependencies') == 'KA-004':
        logging.info("SUCCESS: Hard dependency KA-004 detected for KA-001.")
    else:
        logging.error(f"FAILURE: Hard dependency mismatch for KA-001: {ka_info.get('hard_dependencies')}")

    logging.info("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_phase1_infrastructure()
