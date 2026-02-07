
import os
import sys
import asyncio
from flask import Flask

# Mock flask app for context
app = Flask(__name__)

async def verify():
    print("--- Starting Verification for Google Gemini Integration ---")
    
    # 1. Verify Import
    try:
        from ukg_sdk.providers import GoogleGeminiProvider
        print("[PASS] GoogleGeminiProvider imported successfully")
    except ImportError as e:
        print(f"[FAIL] Could not import GoogleGeminiProvider: {e}")
        return

    # 2. Verify Initialization
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[SKIP] No GOOGLE_API_KEY found in env, skipping live tests")
        return

    try:
        provider = GoogleGeminiProvider(model="gemini-2.5-pro")
        print("[PASS] Provider initialized")
    except Exception as e:
        print(f"[FAIL] Provider initialization failed: {e}")
        return

    # 3. Verify Embedding (via Provider direct)
    try:
        print("Testing Provider Embeddings...")
        emb = await provider.embed("Hello world")
        if emb and len(emb) > 0:
            print(f"[PASS] Embedding generated. Length: {len(emb)}")
        else:
            print("[FAIL] Embedding returned empty")
    except Exception as e:
        print(f"[FAIL] Provider embedding failed: {e}")

    # 4. Verify Chat Completion
    try:
        print("Testing Chat Completion...")
        messages = [{"role": "user", "content": "Hello, are you Gemini?"}]
        response = await provider.complete(messages=messages, model="gemini-2.5-flash")
        print(f"[PASS] Chat response received: {response.text[:50]}...")
    except Exception as e:
        print(f"[FAIL] Chat completion failed: {e}")

    # 5. Verify Gateway Routing Logic (Static check)
    print("\n--- Verifying Gateway Routing ---")
    try:
        from backend.llm_gateway.gateway import LLMGateway
        gateway = LLMGateway()
        
        # Test 1: Complex Reasoning -> Expect GPT-5.2 Pro + Fallbacks (Total ~3)
        print("Test 1: Tier='complex_reasoning' (Expect 3 layers: GPT-5.2 Pro -> Gemini -> Fallback)")
        # Mock env for testing routing purely
        os.environ["OPENAI_API_KEY"] = "sk-test-mock"
        os.environ["GOOGLE_API_KEY"] = "AIza-test-mock"
        
        providers = await gateway._get_eligible_providers(meta={"tier": "complex_reasoning"})
        print(f"   -> Found {len(providers)} providers")
        for i, p in enumerate(providers):
            print(f"      [{i+1}] {p.name} ({p.provider_type}/{p.model_id})")
        
        if len(providers) >= 3:
             print("[PASS] 3-Layer Redundancy confirmed for Complex Reasoning")
        else:
             print(f"[FAIL] Expected 3+ layers, got {len(providers)}")

        # Test 2: RAG Heavy -> Expect Gemini Pro + Fallbacks
        print("\nTest 2: Tier='rag_heavy' (Expect 3 layers: Gemini Pro -> GPT-4.1 -> Flash)")
        providers = await gateway._get_eligible_providers(meta={"tier": "rag_heavy"})
        print(f"   -> Found {len(providers)} providers")
        for i, p in enumerate(providers):
             print(f"      [{i+1}] {p.name} ({p.provider_type}/{p.model_id})")
            
        if len(providers) >= 3:
            print("[PASS] 3-Layer Redundancy confirmed for RAG Heavy")
        else:
            print(f"[FAIL] Expected 3+ layers, got {len(providers)}")
            
        # Test 3: Structured Workflow -> Expect GPT-5 Mini or Gemini Flash
        print("Test 3: Tier='structured_workflow' (Expect GPT-5 Mini)")
        providers = await gateway._get_eligible_providers(meta={"tier": "structured_workflow"})
        top = providers[0]
        print(f"   -> Top Provider: {top.name} | Model: {top.model_id}")
        if "mini" in top.model_id or "flash" in top.model_id:
             print("[PASS] Routing correct for Structured Workflow")
        else:
             print(f"[FAIL] Expected mini/flash, got {top.model_id}")

    except Exception as e:
        print(f"[WARN] Gateway routing test issue: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify())
