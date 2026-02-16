
import logging
import sys
from simulation.layer_controller import LayerController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Pipeline-Verify")

def test_pipeline():
    logger.info("--- Starting Full Pipeline Verification L1->L4 ---")
    
    # 1. Initialize Controller
    controller = LayerController()
    if not controller.initialize_layers():
        logger.error("Failed to initialize layers")
        sys.exit(1)
        
    # 2. Define Query
    query = "Design a HIPAA compliant Python tool for healthcare banking data analysis."
    context = {"query_text": query}
    
    # 3. Run Layer 1 (Planning)
    logger.info(f"Executing L1 with query: '{query}'")
    l1_result = controller.run_layer(1, context)
    
    if "error" in l1_result:
        logger.error(f"L1 Failed: {l1_result['error']}")
        sys.exit(1)
        
    logger.info("✅ L1 Passed. Intent generated.")
    context.update(l1_result) # Pass L1 output to context
    
    # 4. Run Layer 2 (Retrieval)
    logger.info("Executing L2...")
    l2_result = controller.run_layer(2, context)
    
    if "error" in l2_result:
        logger.error(f"L2 Failed: {l2_result['error']}")
        sys.exit(1)
        
    logger.info(f"✅ L2 Passed. Evidence Pack Size: {len(l2_result.get('evidence_pack', {}).get('items', []))}")
    context.update(l2_result) # Pass L2 output to context
    
    # 5. Run Layer 3 (Deep Research)
    logger.info("Executing L3...")
    l3_result = controller.run_layer(3, context)
    
    if "error" in l3_result:
        logger.error(f"L3 Failed: {l3_result['error']}")
        sys.exit(1)

    logger.info("✅ L3 Passed. Augmented Evidence Pack.")
    context.update(l3_result) # Pass L3 output to context

    # 6. Run Layer 4 (POV Engine)
    logger.info("Executing L4 (POV Engine)...")
    try:
        l4_result = controller.run_layer(4, context)
        
        if "error" in l4_result:
             logger.error(f"L4 Failed: {l4_result['error']}")
             sys.exit(1)
             
        logger.info("✅ L4 Passed.")
        # Check if L4 used the evidence (manual check of logs or result structure)
        if 'expanded_context' in l4_result or 'pov_confidence' in l4_result:
             logger.info("L4 output structure valid.")
        else:
             logger.warning("L4 output missing expected keys.")
             
    except Exception as e:
        logger.error(f"❌ L4 CRASHED: {str(e)}")
        sys.exit(1)

    logger.info("🎉 PIPELINE L1-L4 VERIFICATION PASSED")

if __name__ == "__main__":
    test_pipeline()
