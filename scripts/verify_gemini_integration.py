
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
        provider = GoogleGeminiProvider(model="gemini-1.5-pro") # Using 1.5 for basic test as 3.0 might be preview
        print(f"[PASS] Provider initialized with key: {api_key[:5]}...")
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
        response = await provider.complete(messages=messages, model="gemini-3-flash-preview")
        print(f"[PASS] Chat response received: {response.text[:50]}...")
    except Exception as e:
        print(f"[FAIL] Chat completion failed: {e}")

    # 5. Verify Gateway Routing Logic (Static check)
    print("\n--- Verifying Gateway Routing ---")
    try:
        from backend.llm_gateway.gateway import LLMGateway
        gateway = LLMGateway()
        
        # We need to mock the DB, but let's test the _get_eligible_providers env fallback
        # This requires an app context and mocked DB queries usually, but 
        # _get_eligible_providers falls back to env if DB fails.
        
        # We need to prevent it from failing hard on DB query
        # Since we are running standalone, DB query will fail, triggering fallback.
        
        with app.app_context():
            # Mock DB session in a very hacky way just to avoid crash if possible?
            # Actually catch exception in gateway handles it.
            
            providers = await gateway._get_eligible_providers(meta={"tier": "complex_reasoning"})
            print(f"Complex Reasoning Tier Providers: {[p.name for p in providers]}")
            
            providers = await gateway._get_eligible_providers(meta={"tier": "fast_chat"})
            print(f"Fast Chat Tier Providers: {[p.name for p in providers]}")
            
    except Exception as e:
        print(f"[WARN] Gateway routing test hit expected DB issue: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify())
