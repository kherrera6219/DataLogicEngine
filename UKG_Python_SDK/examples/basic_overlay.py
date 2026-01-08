import asyncio

from ukg_sdk import UKGOverlay
from ukg_sdk.providers import OpenAIProvider


async def main():
    ukg = UKGOverlay(provider=OpenAIProvider(), model="gpt-4.1-mini")
    result = await ukg.run(
        query="Explain the UKG tier router in one paragraph.",
        user_id="demo",
        meta={"pillar": "PL-001", "axis2": "NAICS", "date": "2026-01-05"},
    )
    print(result["answer"])
    print("tier:", result["tier"])
    print("coordinate:", result["coordinate"])


if __name__ == "__main__":
    asyncio.run(main())
