import asyncio

from ukg_sdk import UKGOverlay


async def main() -> None:
    client = UKGOverlay(base_url="http://127.0.0.1:5000/api/v1")
    result = await client.run(
        query="Explain the governed tier router in one paragraph.",
        meta={"source": "basic_overlay_example"},
    )
    print(result["answer"])
    print("trace:", result["trace_id"])


if __name__ == "__main__":
    asyncio.run(main())
