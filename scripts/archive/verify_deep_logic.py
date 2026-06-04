"""
Verification Script for Deep Logic (Layer 6 & KA Integration)
"""
import sys
import os
import logging
from pprint import pprint

# Ensure we can import from root
sys.path.append(os.getcwd())

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyDeepLogic")

def verify_refinement_workflow():
    logger.info("=== Verifying Refinement Workflow ===")
    from core.simulation.refinement_workflow import create_refinement_workflow
    
    workflow = create_refinement_workflow()
    
    query = {
        "query_id": "TEST-QUERY-001",
        "query": "What are the compliance risks of AI in finance?",
        "confidence": 0.5
    }
    
    logger.info("Executing workflow...")
    result = workflow.execute_workflow(query)
    
    pprint(result)
    
    # Check specific KA outputs
    steps = result.get("steps_completed", [])
    
    # Check KA-001 (AoT) results
    step1 = next((s for s in steps if s["step_id"] == "step1_aot"), None)
    if step1 and step1["state_updates"].get("success"):
        logger.info("✅ KA-001 (AoT) Executed Successfully")
    else:
        logger.error("❌ KA-001 (AoT) Failed")

    # Check KA-007 (Synthesis) results
    step12 = next((s for s in steps if s["step_id"] == "step12_final_synthesis"), None)
    if step12 and step12["state_updates"].get("success"):
        logger.info("✅ KA-007 (Synthesis) Executed Successfully")
    else:
        logger.error("❌ KA-007 (Synthesis) Failed")

def verify_layer6():
    logger.info("\n=== Verifying Layer 6 (Neural Analysis) ===")
    from core.simulation.layer6_neural_analysis import Layer6NeuralAnalysis
    
    l6 = Layer6NeuralAnalysis()
    
    # Simulated Layer 5 Output
    consensus_data = {
        "debate_results": ["A", "B", "A"],
        "consensus_score": 0.9,
        "covered_axes": [1, 2, 3, 5], # Missing critical axes
        "content": "Low risk detected but compliance uncertain."
    }
    
    result = l6.process(consensus_data)
    pprint(result)
    
    if result["patterns_detected"]:
        logger.info("✅ Detect Patterns: Success")
    else:
        logger.warning("⚠️ Detect Patterns: No patterns found")

    if result["gaps_identified"]:
        logger.info("✅ Gap Analysis: Success (Identified gaps)")
    else:
        logger.error("❌ Gap Analysis: Failed")

    if result["synthesis"]:
        logger.info("✅ Synthesis: Success")
    else:
        logger.error("❌ Synthesis: Failed")

if __name__ == "__main__":
    verify_refinement_workflow()
    verify_layer6()
