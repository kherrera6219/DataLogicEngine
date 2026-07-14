"""Compatibility entry point for the owner-run Google availability check."""

from __future__ import annotations

import asyncio
import os

from backend.llm_gateway.model_defaults import GOOGLE_PRIMARY_MODEL
from backend.llm_gateway.providers import GoogleProvider


async def verify() -> int:
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("[SKIP] Google API key is not configured")
        return 2
    provider = GoogleProvider()
    try:
        response = await asyncio.wait_for(
            provider.complete(
                messages=[{"role": "user", "content": "Reply with exactly: pong"}],
                model=GOOGLE_PRIMARY_MODEL,
                temperature=0,
                max_tokens=16,
            ),
            timeout=30,
        )
        print(f"[PASS] Google model available: {response.model}")
        return 0
    finally:
        await provider.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(verify()))
