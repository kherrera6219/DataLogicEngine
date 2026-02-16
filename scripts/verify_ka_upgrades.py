
import asyncio
import unittest.mock
import json
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def verify_ka117_threat_model():
    print("\n=== Verifying KA-117 (Threat Model) Upgrade ===")
    from backend.knowledge_algorithms.ka_117_threat_model_agent import KA117ThreatModelAgent
    
    # Explicit import to ensure module is loaded for patching
    
    # Mock Gateway
    with unittest.mock.patch('backend.llm_gateway.gateway.get_gateway') as MockGetGateway:
        mock_gateway = unittest.mock.AsyncMock()
        MockGetGateway.return_value = mock_gateway
        
        # Setup mock response
        mock_response = unittest.mock.Mock()
        mock_response.content = json.dumps({
            "system_name": "Test System",
            "threats": [
                {
                    "category": "Spoofing",
                    "threat": "Fake User",
                    "impact": "Low",
                    "mitigation": "MFA",
                    "severity": "Medium"
                }
            ],
            "overall_risk_score": 50
        })
        mock_gateway.process.return_value = mock_response
        
        agent = KA117ThreatModelAgent({})
        # Verify using ASYNC method directly to avoid loop conflict
        result = await agent._run_logic_async({"system_description": "A web login form"})
        
        print(f"Result: {result}")
        
        if result['status'] == 'success' and result['threat_model']['system_name'] == "Test System":
            print("[PASS] KA-117 correctly used Gateway result")
        else:
            print("[FAIL] KA-117 did not return expected Gateway result")

async def verify_ka005_classification():
    print("\n=== Verifying KA-005 (Classification) Upgrade ===")
    from backend.knowledge_algorithms.ka_05_query_classification import KA005QueryClassification
    
    # Explicit import to ensure module is loaded for patching

    # Mock Gateway
    with unittest.mock.patch('backend.llm_gateway.gateway.get_gateway') as MockGetGateway:
        mock_gateway = unittest.mock.AsyncMock()
        MockGetGateway.return_value = mock_gateway
        
        # Setup mock response
        mock_response = unittest.mock.Mock()
        mock_response.content = json.dumps({
            "category": "ACCESS_CONTROL",
            "confidence": 0.99
        })
        mock_gateway.process.return_value = mock_response
        
        algo = KA005QueryClassification({})
        # Use underlying gateway method directly for test
        # Note: We need to bypass the _run_logic -> _delegate_to_sdk chain 
        # because KA-005 structure is hard to verify async without full refactor.
        # So we verify the _classify_via_gateway method directly.
        result = await algo._classify_via_gateway("reset password")
        
        print(f"Result: {result}")
        
        if result['category'] == "ACCESS_CONTROL" and result['confidence'] == 0.99:
             print("[PASS] KA-005 correctly used Gateway result")
        else:
             print("[FAIL] KA-005 did not return expected Gateway result")

async def run_all():
    await verify_ka117_threat_model()
    await verify_ka005_classification()

if __name__ == "__main__":
    asyncio.run(run_all())
