"""Owner-run live availability checks for the two supported providers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from backend.llm_gateway.provider_errors import classify_provider_failure  # noqa: E402
from backend.llm_gateway.provider_manifest import PROVIDERS  # noqa: E402
from backend.llm_gateway.providers import GoogleProvider, OpenAIProvider  # noqa: E402


@dataclass(frozen=True, slots=True)
class ProviderCheck:
    provider: str
    status: str
    model: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "available"


async def _check(provider_id: str) -> ProviderCheck:
    definition = next(provider for provider in PROVIDERS if provider.id == provider_id)
    configured = any(os.environ.get(name) for name in definition.api_key_environment)
    if not configured:
        return ProviderCheck(provider_id, "not_configured", definition.default_model, "No API key configured")

    adapter = OpenAIProvider() if provider_id == "openai" else GoogleProvider()
    try:
        await asyncio.wait_for(
            adapter.complete(
                messages=[{"role": "user", "content": "Reply with exactly: pong"}],
                model=definition.default_model,
                temperature=0,
                max_tokens=16,
            ),
            timeout=30,
        )
        return ProviderCheck(provider_id, "available", definition.default_model, "Live generation succeeded")
    except Exception as exc:
        failure = classify_provider_failure(exc)
        limited = failure.failure_class.value in {"rate_limited", "quota_exhausted", "billing_suspended"}
        invalid = failure.failure_class.value in {"invalid_key", "invalid_model", "unauthorized_model"}
        status = "limited" if limited else ("invalid" if invalid else "unavailable")
        return ProviderCheck(provider_id, status, definition.default_model, failure.failure_class.value)
    finally:
        await adapter.close()


async def _main() -> int:
    checks = [await _check(provider.id) for provider in PROVIDERS]
    for check in checks:
        print(f"{check.provider}: {check.status} ({check.model}) - {check.detail}")
    configured = [check for check in checks if check.status != "not_configured"]
    return 0 if configured and all(check.ok for check in configured) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
