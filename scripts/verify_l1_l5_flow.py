
import logging
import sys
from datetime import datetime
from simulation.layer_controller import LayerController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Pipeline-Verify-L1-L5")

def test_pipeline_full():
    logger.info("--- Starting Full Pipeline Verification L1->L5 ---")
    
    # 1. Initialize Controller
    controller = LayerController()
    if not controller.initialize_layers():
        logger.error("Failed to initialize layers")
        sys.exit(1)
        
    # 2. Define Query
    # Using a query that triggers multiple axes (Regulatory, Compliance, Sector, etc.)
    query = "Design a HIPAA compliant Python tool for healthcare banking data analysis on AWS."
    context = {"query_text": query}
    
    # 3. Run Layer 1 (Planning)
    logger.info(f"Executing L1 with query: '{query}'")
    l1_result = controller.run_layer(1, context)
    if "error" in l1_result:
        logger.error(f"L1 Failed: {l1_result['error']}")
        sys.exit(1)
    logger.info("✅ L1 Passed.")
    context.update(l1_result) 
    
    # 4. Run Layer 2 (Retrieval)
    logger.info("Executing L2...")
    l2_result = controller.run_layer(2, context)
    if "error" in l2_result:
        logger.error(f"L2 Failed: {l2_result['error']}")
        sys.exit(1)
    logger.info(f"✅ L2 Passed. Evidence items: {len(l2_result.get('evidence_pack', {}).get('items', []))}")
    context.update(l2_result)
    
    # 5. Run Layer 3 (Deep Research)
    logger.info("Executing L3...")
    l3_result = controller.run_layer(3, context)
    if "error" in l3_result:
        logger.error(f"L3 Failed: {l3_result['error']}")
        sys.exit(1)
    logger.info("✅ L3 Passed.")
    context.update(l3_result)

    # 6. Run Layer 4 (POV Engine)
    logger.info("Executing L4 (POV Engine)...")
    l4_result = controller.run_layer(4, context)
    if "error" in l4_result:
         logger.error(f"L4 Failed: {l4_result['error']}")
         sys.exit(1)
    logger.info("✅ L4 Passed.")
    context.update(l4_result)

    # 7. Run Layer 5 (Integration Engine - NEW)
    logger.info("Executing L5 (Integration Engine)...")
    l5_result = controller.run_layer(5, context)
    if "error" in l5_result:
         logger.error(f"L5 Failed: {l5_result['error']}")
         sys.exit(1)
    
    if l5_result.get("layer5_processed"):
        consensus = l5_result.get("layer5_consensus", {})
        status = consensus.get("status")
        conf = consensus.get("confidence_sys")
        personas = l5_result.get("layer5_personas", [])
        
        logger.info(f"✅ L5 Passed.")
        logger.info(f"   Status: {status}")
        logger.info(f"   Confidence: {conf}")
        logger.info(f"   Personas: {personas}")
        
        # Validation checks
        if status not in ["FINALIZE", "ESCALATE", "BLOCK", "REDACT", "CLARIFY"]:
            logger.error(f"❌ Invalid L5 Status: {status}")
            sys.exit(1)
            
        if len(personas) == 0:
            logger.error("❌ No personas spawned in L5")
            sys.exit(1)
            
    else:
        logger.error("❌ L5 did not return 'layer5_processed' flag.")
        logger.error(f"Result dump: {l5_result.keys()}")
        sys.exit(1)

    logger.info("🎉 FULL PIPELINE L1-L5 VERIFICATION PASSED")

if __name__ == "__main__":
    test_pipeline_full()
