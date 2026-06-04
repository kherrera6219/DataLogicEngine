
import logging
import sys
from core.simulation.layer5_legacy_integration import Layer5IntegrationEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("L5-Verify")

def test_layer5_graph():
    logger.info("--- Starting Layer 5 (LangGraph) Verification ---")
    
    # 1. Initialize Engine
    try:
        engine = Layer5IntegrationEngine()
        logger.info("✅ Engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize engine: {e}")
        sys.exit(1)

    # 2. Mock Context (Simulating L1-L4 output)
    # We purposefully trigger REGULATORY persona by including 'a6' (Regulatory Axis)
    mock_context = {
        "session_id": "verify-session-123",
        "intent": {
            "query_text": "How do I store HIPAA compliant data in AWS?",
            "a6": "hipaa_compliance", # Triggers Regulatory
            "a7": "data_privacy"      # Triggers Compliance
        },
        "evidence_pack": {
            "items": [
                {"id": "ev1", "content": "HIPAA requires encryption at rest."},
                {"id": "ev2", "content": "AWS S3 supports AES-256."}
            ]
        },
        "content": "Initial draft answer based on retrieval.",
        "confidence_score": 0.6 # Low confidence to trigger deeper check
    }

    # 3. Run Process
    logger.info("Execute process()...")
    result = engine.process(mock_context)
    
    # 4. Assertions
    if result.get("layer5_error"):
        logger.error(f"❌ Layer 5 Error: {result['layer5_error']}")
        sys.exit(1)

    consensus = result.get("layer5_consensus", {})
    personas = result.get("layer5_personas", [])
    outputs = result.get("layer5_outputs", [])
    
    logger.info(f"Consensus Status: {consensus.get('status')}")
    logger.info(f"System Confidence: {consensus.get('confidence_sys')}")
    logger.info(f"Personas Spawned: {personas}")
    
    # Check if correct personas were spawned
    expected_personas = {"KNOWLEDGE", "REGULATORY", "COMPLIANCE"}
    spawned_set = set(personas)
    
    if not expected_personas.issubset(spawned_set):
        logger.warning(f"⚠️ Expected personas {expected_personas} but got {spawned_set}")
    else:
        logger.info("✅ Core personas spawned correctly.")
        
    # Check output structure
    if len(outputs) > 0:
        logger.info(f"✅ Received {len(outputs)} persona outputs.")
        first_claims = outputs[0].get("claims", [])
        if first_claims:
             logger.info(f"   Sample Claim: {first_claims[0].get('text')}")
    else:
        logger.error("❌ No persona outputs generated.")
        sys.exit(1)

    if result.get("layer5_processed"):
        logger.info("🎉 Layer 5 Graph Verification PASSED")
    else:
        logger.error("❌ 'layer5_processed' flag missing.")

if __name__ == "__main__":
    test_layer5_graph()
