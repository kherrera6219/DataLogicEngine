import asyncio
import os
import logging
from ukg_sdk import UKGOverlay
from ukg_sdk.providers import OpenAIProvider

# Configure logging to see the new structured logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ukg_sdk")
logger.setLevel(logging.DEBUG)

async def main():
    print("🚀 UKG SDK Quickstart")
    print("---------------------")

    # 1. Setup Provider (Expects OPENAI_API_KEY env var)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found. Using dummy provider for demonstration.")
        # In a real app, you'd raise an error or prompt the user.
        
    class DummyProvider(OpenAIProvider):
        async def complete(self, messages, **kwargs):
            from ukg_sdk.providers import LLMResponse
            return LLMResponse(text="This is a simulated response from the UKG Overlay.", model="sim-gpt", usage={"tokens": 10}, raw={})

    provider = DummyProvider(api_key="dummy") if not api_key else OpenAIProvider()

    # 2. Initialize Overlay
    overlay = UKGOverlay(
        provider=provider,
        model="gpt-4o",
        actor="quickstart-user"
    )

    # 3. Run a Query
    query = "Explain the difference between a TruthGate and a TruthCore."
    print(f"\n❓ Query: {query}")
    
    result = await overlay.run(
        query=query,
        user_id="demo-user",
        meta={"source": "quickstart"}
    )

    # 4. Inspect Results
    if result["ok"]:
        print("\n✅ Answer:", result["answer"])
        print(f"   Coordinate: {result['coordinate']}")
        print(f"   Tier: {result['tier']}")
    else:
        print("\n❌ Error:", result["error"])

if __name__ == "__main__":
    asyncio.run(main())
