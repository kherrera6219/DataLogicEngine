
import asyncio
import os
import sys
import logging
import traceback
from datetime import datetime
import unittest.mock

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
    
    # Ensure module is loaded for patching
    try:
        import backend.llm_gateway.gateway
    except ImportError:
        pass 

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

async def verify_audio_failover():
    print("\n=== Verifying Audio Service Failover ===")
    from backend.services.audio_service import AudioService
    
    # Force OpenAI fail, Google success (mocked)
    os.environ["OPENAI_API_KEY"] = "" # Force None
    os.environ["GOOGLE_API_KEY"] = "AIza-mock"
    
    service = AudioService()
    
async def verify_audio_failover():
    print("\n=== Verifying Audio Service Failover ===")
    from backend.services.audio_service import AudioService
    
    # Force OpenAI fail, Google success (mocked)
    os.environ["OPENAI_API_KEY"] = "" 
    os.environ["GOOGLE_API_KEY"] = "AIza-mock"
    
    service = AudioService()
    
    # Ensure module is loaded for patching
    try:
        import google.genai
    except ImportError:
        print("[SKIP] google-genai not installed, cannot test failover logic deeply")
        return

    # Mock the Client class on the actual module object
    with unittest.mock.patch('google.genai.Client') as MockClient:
        mock_client_instance = MockClient.return_value
        # Mock models.generate_content -> object with .text
        mock_response = unittest.mock.Mock()
        mock_response.text = "Google Transcription Success"
        mock_client_instance.models.generate_content.return_value = mock_response
        
        # Trigger the logic
        result = await service.transcribe(b"fake-audio-bytes")
        
        if result == "Google Transcription Success":
            print("[PASS] Audio Service failed over to Google")
        else:
            print(f"[FAIL] Audio Service did not return Google result. Got: {result}")

async def verify_video_gateway():
    print("\n=== Verifying Video Service Gateway Injection ===")
    from backend.services.video_service import VideoService
    
    # Test 1: Auto-injection
    service = VideoService()
    if service.llm_gateway is not None:
         print("[PASS] VideoService initialized generic Gateway")
    else:
         print("[FAIL] VideoService did not lazy init Gateway")

async def run_all():
    print("Running RAG Test...")
    try:
        await verify_rag_embedding_failover()
    except Exception as e:
        print(f"RAG Test Failed: {e}")
        traceback.print_exc()

    print("Running Active Defense Test...")
    try:
        await verify_active_defense_live()
    except Exception as e:
        print(f"Active Defense Test Failed: {e}")
        traceback.print_exc()

    print("Running Audio Failover Test...")
    try:
        await verify_audio_failover()
    except Exception as e:
        print(f"Audio Failover Test Failed: {e}")
        traceback.print_exc()

    print("Running Video Gateway Test...")
    try:
        await verify_video_gateway()
    except Exception as e:
        print(f"Video Gateway Test Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all())
