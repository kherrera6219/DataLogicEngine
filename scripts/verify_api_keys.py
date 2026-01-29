
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load env vars first
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv('.env')

async def check_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"Checking OpenAI Key (Length: {len(api_key) if api_key else 0})...")
    if not api_key:
        print("[FAIL] OPENAI_API_KEY not found or empty.")
        return False
        
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        
        # New 2026 Pattern: Responses API
        target_model = "gpt-5.2"
        print(f"   > Testing generation with: {target_model} (Responses API)")
        
        try:
            response = await client.responses.create(
                model=target_model,
                input="ping",
                max_output_tokens=5
            )
            print(f"[PASS] OpenAI API Key is valid. (Model: {target_model})")
            return True
        except Exception as e:
            print(f"[FAIL] OpenAI Generation Error: {e}")
            return False

    except Exception as e:
        print(f"[FAIL] OpenAI Client Error: {e}")
        return False
        
async def check_google():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    print(f"Checking Google/Gemini API Key (Length: {len(api_key) if api_key else 0})...")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY or GOOGLE_API_KEY not found or empty.")
        return False
        
    try:
        # NEW SDK: google-genai
        from google import genai
        
        version = getattr(genai, "__version__", "unknown")
        print(f"   > Using 'google-genai' SDK version: {version}")
        
        # User snippet uses 'genai.Client(api_key=...)'
        client = genai.Client(api_key=api_key)
        
        # Test Gemini 3 Pro Preview as requested
        target_model = "gemini-3-pro-preview"
        print(f"   > Testing generation with: {target_model}")
        
        try:
            # User snippet: response = client.models.generate_content(...)
            response = client.models.generate_content(
                model=target_model,
                contents="Explain the standard model of physics in one sentence."
            )
            print(f"[PASS] Google Gemini API Key is valid. (Model: {target_model})")
            return True
        except Exception as e:
            print(f"[FAIL] Generation failed for {target_model}: {e}")
            return False

    except ImportError:
        print("[FAIL] 'google-genai' SDK not installed. Run: pip install -U google-genai")
        return False
    except Exception as e:
        print(f"[FAIL] Google Client Error: {e}")
        return False

async def main():
    print("=== Robust API Key Verification (Best Practices) ===\n")
    openai_status = await check_openai()
    print("-" * 30)
    google_status = await check_google()
    print("\n=== Summary ===")
    print(f"OpenAI: {'PASS' if openai_status else 'FAIL'}")
    print(f"Google: {'PASS' if google_status else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
