"""
Verification Script for Layer 3 (Deep Research Agent)
Tests:
1. KA operation (Claim Extraction, Research)
2. Layer3AgentEngine (Tier Routing)
3. LayerController Integration
"""

import sys
import os
import json
import logging

# Setup Path
sys.path.append(r"c:\software\DataLogicEngine")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("L3-Verify")

def test_models():
    logger.info("--- Testing Models ---")
    from quad_persona.quad_models import EvidenceItem, EvidencePack
    
    item = EvidenceItem(content="Test Fact", source_uri="http://example.com")
    pack = EvidencePack()
    pack.add_item(item)
    
    data = pack.to_dict()
    assert data["items"][0]["content"] == "Test Fact"
    logger.info("✅ Models OK")

def test_kas():
    logger.info("--- Testing Knowledge Algorithms ---")
    
    # Tier 1
    from backend.knowledge_algorithms.ka_claim_extraction import KAClaimExtraction
    ka1 = KAClaimExtraction()
    # Sentences must be > 20 chars to pass noise filter
    text = "The sky is usually blue during the day. Water is generally considered wet by most people."
    res1 = ka1.execute({"text": text, "source_uri": "test"})
    
    if not res1["success"]:
        logger.error(f"KA1 Failed: {res1}")
    
    # Debug info
    logger.info(f"KA1 Extracted: {len(res1['evidence_items'])} items")
    
    assert len(res1["evidence_items"]) == 2
    logger.info("✅ KA-ClaimExtraction OK")
    
    # Tier 3
    from backend.knowledge_algorithms.ka_29_online_validation import KAResearch
    ka3 = KAResearch({"delay_ms": 10})
    res3 = ka3.execute({"query": "cyber requirements", "domain": "test"})
    assert res3["success"]
    assert len(res3["evidence_items"]) > 0
    assert "content" in res3["evidence_items"][0]
    logger.info("✅ KA-Research OK")

def test_engine():
    logger.info("--- Testing Layer 3 Agent Engine ---")
    from simulation.layer3_agent_engine import Layer3AgentEngine
    
    engine = Layer3AgentEngine({"delay_ms": 10})
    
    # Test Tier 3 Request
    intent = {"description": "Find F-22 specs"}
    plan = {"tier": 3}
    context = {"query_text": "Find F-22 specs"}
    
    pack = engine.process_request(intent, plan, context)
    
    data = pack.to_dict()
    assert data["research_tier"] == "tier3"
    assert len(data["items"]) > 0
    logger.info("✅ Layer 3 Engine (Tier 3) OK")

def test_controller():
    logger.info("--- Testing Layer Controller Integration ---")
    from simulation.layer_controller import LayerController
    
    ctrl = LayerController()
    
    context = {
        "intent": {"description": "Verify HIPAA compliance"},
        "tier_plan": {"tier": 3},
        "query_text": "Verify HIPAA compliance"
    }
    
    # Run Layer 3
    result = ctrl.run_layer(3, context)
    
    assert result["success"]
    assert "evidence_pack" in result
    pack = result["evidence_pack"]
    assert len(pack["items"]) > 0
    logger.info("✅ Layer Controller -> L3 OK")

if __name__ == "__main__":
    try:
        test_models()
        test_kas()
        test_engine()
        test_controller()
        logger.info("\n🎉 AUTOMATED VERIFICATION PASSED: Layer 3 is operational.")
    except Exception as e:
        logger.error(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
