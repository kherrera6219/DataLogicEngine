import asyncio
import os

from ukg_sdk import UKGOverlay


async def main() -> None:
    overlay = UKGOverlay(
        base_url=os.getenv(
            "DATALOGICENGINE_API_URL",
            "http://127.0.0.1:5000/api/v1",
        ),
        api_key=os.getenv("DATALOGICENGINE_API_KEY"),
    )
    result = await overlay.run(
        query="Explain the difference between TruthGate and TruthCore.",
        user_id="quickstart-user",
        meta={"source": "sdk_quickstart"},
    )
    print(result["answer"])
    print("trace:", result["trace_id"])
    print("status:", result["status"])


if __name__ == "__main__":
    asyncio.run(main())
