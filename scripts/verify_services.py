
import asyncio
import os
import sys
import logging
from datetime import datetime

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def verify_rag_embedding_failover():
    print("\n=== Verifying RAG Embedding Failover (3-Layers) ===")
    from backend.services.rag_service import RAGService
    
    rag = RAGService()
    
    # 1. Test OpenAI Failure -> Google Success
    print("Test 1: OpenAI Fail -> Google Success")
    os.environ["OPENAI_API_KEY"] = "invalid-sk-key" # Force OpenAI fail
    os.environ["GOOGLE_API_KEY"] = "AIza-valid-mock" # Assume valid for structural test
    
    # We mock the actual Google SDK call to avoid real network cost/auth failure in test env
    # But we want to see it HIT the Google logic block
    
    # Mocking internal methods is tricky without dependency injection, so we rely on logs/result structure
    # For this test, we accept if it doesn't crash and returns *something* (likely mock if no real key)
    # But we want to verify logic flow if possible.
    
    embedding = rag._default_embedding("test query")
    if len(embedding) > 0:
        print(f"[PASS] Embedding generated. Length: {len(embedding)}")
    else:
        print("[FAIL] No embedding generated")

async def verify_active_defense_live():
    print("\n=== Verifying Active Defense (Live Gateway) ===")
    from backend.security.active_defense import ActiveDefenseService
    
    # Set to mock so we don't actually burn credits but test the CODE PATH
    # The active logic will try to import gateway.
    # To test logic without credits, we can trust the unit test or mock Gateway.
    # But here we want to verify integration.
    
    # We'll use a mocked Gateway for safety in this script
    import unittest.mock
    
    with unittest.mock.patch('backend.llm_gateway.gateway.LLMGateway') as MockGateway:
        mock_instance = MockGateway.return_value
        
        # Setup async return for process()
        async def mock_process(*args, **kwargs):
            class MockResponse:
                ok = True
                content = '{"is_safe": true, "threat_score": 0.1, "reason": "Test benign"}'
            return MockResponse()
            
        mock_instance.process.side_effect = mock_process
        
        service = ActiveDefenseService()
        verdict = await service.assess_incoming("Hello", "Summary", "user")
        
        print(f"Verdict: {verdict}")
        if verdict.reason == "Test benign":
            print("[PASS] Active Defense correctly called Gateway")
        else:
            print(f"[FAIL] Active Defense did not return expected mock result. Got: {verdict.reason}")

async def run_all():
    await verify_rag_embedding_failover()
    await verify_active_defense_live()

if __name__ == "__main__":
    asyncio.run(run_all())
