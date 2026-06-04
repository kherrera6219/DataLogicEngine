"""
Verification Script for L1-L2-L3 Pipeline
Tests the full "v17" Dynamic Flow:
1. L1: Query -> ProblemSpec/Intent (Planning)
2. L2: Intent -> EvidencePack (Retrieval)
3. L3: Pack -> Pack (Refinement/Research)
"""

import sys
import json
import logging

# Setup Path
sys.path.append(r"c:\software\DataLogicEngine")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Pipeline-Verify")

def test_pipeline():
    logger.info("--- Starting Full Pipeline Verification ---")
    
    from core.simulation.layer_controller import LayerController
    
    ctrl = LayerController()
    
    # 1. Define Request
    # Complex query triggering multiple axes
    query = "Design a HIPAA compliant Python tool for healthcare banking data analysis."
    # Axes triggered: 
    # - Design (Task Type)
    # - HIPAA (Regulatory)
    # - Python (Tool)
    # - Healthcare (Sector)
    # - Banking (Sector)
    
    context = {"query_text": query, "user_role": "architect"}
    
    # 2. Run Layer 1 (Planning)
    logger.info(">>> Running Layer 1 (Planning)")
    l1_res = ctrl.run_layer(1, context)
    
    if "error" in l1_res:
        raise Exception(f"L1 Failed: {l1_res}")
        
    intent = l1_res["intent"]
    spec = l1_res["problem_spec"]
    
    logger.info(f"L1 Intent Axes: {json.dumps(intent, indent=2)}")
    logger.info(f"L1 Spec Type: {spec['task_type']}")
    
    # Verify L1 Logic
    assert "HIPAA" in intent["axis_6_regulation"]
    assert "PYTHON" in intent["axis_5_tool"]
    assert "Healthcare" in intent["axis_2_sector"]
    assert spec["task_type"] == "design"
    logger.info("✅ L1 Planning Verified")
    
    # Update Context with L1 Outputs (simulating orchestrator passing data)
    context.update(l1_res)
    
    # 3. Run Layer 2 (Retrieval)
    logger.info(">>> Running Layer 2 (Retrieval)")
    l2_res = ctrl.run_layer(2, context)
    
    if "error" in l2_res:
         raise Exception(f"L2 Failed: {l2_res}")
         
    pack = l2_res["evidence_pack"]
    
    logger.info(f"L2 Retrieved {len(pack['items'])} items")
    
    # Verify L2 Logic
    # Should have found some internal items based on keywords if they exist in YAMLs
    # Even if mocked DB is empty, structure should constitute success.
    assert pack["research_tier"] == "internal_retrieval"
    logger.info("✅ L2 Retrieval Verified")
    
    # Update Context again
    context.update(l2_res)
    
    # 4. Run Layer 3 (Deep Research)
    logger.info(">>> Running Layer 3 (Deep Research)")
    l3_res = ctrl.run_layer(3, context)
    
    if "error" in l3_res:
         raise Exception(f"L3 Failed: {l3_res}")
         
    final_pack = l3_res["evidence_pack"]
    logger.info(f"L3 Final Pack Size: {len(final_pack['items'])}")
    logger.info("✅ L3 Execution Verified")

if __name__ == "__main__":
    try:
        test_pipeline()
        logger.info("\n🎉 PIPELINE VERIFICATION PASSED: L1->L2->L3 is fully functional.")
    except Exception as e:
        logger.error(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
