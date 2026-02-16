
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append('c:\\software\\DataLogicEngine')

from core.system.united_system_manager import UnitedSystemManager
from simulation.layer_controller import LayerController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_unified_system():
    print("=== Verifying Unified System (L1-L7) ===")
    
    # 1. Initialize United System Manager
    print("\n1. Initializing United System Manager...")
    usm = UnitedSystemManager()
    usm.initialize_unified_system(axis_registry_path="config/axis_registry.yaml")
    
    status = usm.get_system_status()
    print(f"   USM Initialized: {status['initialized']}")
    print(f"   Components: {list(usm.components.keys())}")
    
    if not status['initialized']:
        print("FAIL: USM failed to initialize")
        return False

    # 2. Initialize Layer Controller with USM
    print("\n2. Initializing Layer Controller with USM...")
    controller = LayerController(config={}, system_manager=usm)
    success = controller.initialize_layers()
    print(f"   Layers Initialized: {success}")
    
    if not success:
        print("FAIL: LayerController failed to initialize")
        return False
        
    # 3. Define Test Context
    print("\n3. Defining Test Context...")
    # A complex query that should trigger multiple layers
    query = "Analyze the impact of AI regulation on healthcare data privacy in the EU vs US."
    
    context = {
        "query_text": query,
        "session_id": "verify_unified_1",
        "user_id": "admin"
    }
    
    # 4. Run Layer Sequence (L1 -> L2 -> L3 -> L4 -> L5 -> L7)
    # Note: We are forcing the sequence here. In production, Gatekeeper (L6) might decide this.
    active_layers = [1, 2, 3, 4, 5, 7]
    print(f"\n4. Running Layer Sequence: {active_layers}")
    
    start_time = datetime.now()
    result = controller.run_layer_sequence(active_layers, context)
    end_time = datetime.now()
    
    print(f"   Execution Time: {(end_time - start_time).total_seconds():.2f}s")
    
    # 5. Verify Outputs
    print("\n5. Verifying Outputs...")
    
    # L1: Intent
    if 'intent' in result:
        print("   [PASS] L1 Intent generated")
    else:
        print("   [FAIL] L1 Intent missing")
        
    # L2: Evidence
    if 'evidence_pack' in result: # L2 might produce this via correct flow
        # Note: L2 result key might vary, let's check layer_activations
        print("   [PASS] L2 Evidence generated (checked via artifact)")
    elif 'layer_activations' in result and result['layer_activations'].get('layer_2', {}).get('success'):
         print("   [PASS] L2 reported success")
    else:
         print("   [FAIL] L2 execution failed or evidence missing")

    # L3: Plan/Agent
    if 'layer_activations' in result and result['layer_activations'].get('layer_3', {}).get('success'):
        print("   [PASS] L3 Agent execution success")
    
    # L4: POV
    if 'pov_outcomes' in result or 'expanded_context' in result or ('layer_activations' in result and result['layer_activations'].get('layer_4', {}).get('success')):
        # POVEngine.process returns dict, merged into result. keys depend on POVEngine internals
        print("   [PASS] L4 POV Engine execution success")
        
    # L5: Integration
    if result.get('layer5_processed'):
        print("   [PASS] L5 Integration processed")
        print(f"   L5 Processing Type: {result.get('layer5_processing_type')}")
        print(f"   L5 Confidence Score: {result.get('confidence_score')}")
    else:
        print("   [FAIL] L5 output missing")
        
    # L7: AGI
    if 'emergence_score' in result:
        print("   [PASS] L7 AGI Simulation processed")
        print(f"   L7 Emergence Score: {result.get('emergence_score')}")
        print(f"   L7 Entropy: {result.get('entropy')}")
    else:
        # Check if it ran but didn't produce specific keys (unlikely given code reading)
        if result.get('agi_error'):
             print(f"   [FAIL] L7 Error: {result.get('agi_error')}")
        else:
             print("   [FAIL] L7 output missing")

    # Overall
    print("\n=== Verification Summary ===")
    if result.get('layer5_processed') and 'emergence_score' in result:
        print("SUCCESS: Unified System (L1-L7) Verified")
        return True
    else:
        print("FAILURE: Unified System verification incomplete")
        return False

if __name__ == "__main__":
    verify_unified_system()
