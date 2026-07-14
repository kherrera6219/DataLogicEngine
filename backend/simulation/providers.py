"""Provider-only implementations for the authoritative simulation engine."""

from __future__ import annotations

import hashlib
from typing import Any


class FixedSeedSimulationTurnProvider:
    """Deterministic, network-free provider used only for qualification runs."""

    provider_type = "deterministic"
    model = "fixed-seed-v1"
    pricing_status = "available"

    def __init__(self, *, seed: int) -> None:
        self.seed = int(seed)

    async def generate_turn(
        self,
        *,
        prompt: str,
        persona: str,
        max_tokens: int,
        simulation_id: str,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(
            f"{self.seed}:{persona}:{prompt}".encode("utf-8")
        ).hexdigest()[:16]
        content = (
            f"Qualification observation {digest} from {persona}. "
            "This fixed-seed output validates workflow determinism and is not external evidence."
        )
        return {
            "content": content,
            "provider": self.provider_type,
            "model": self.model,
            "tokens_in": max(1, (len(prompt) + 3) // 4),
            "tokens_out": max(1, (len(content) + 3) // 4),
            "estimated_cost_usd": 0.0,
        }


class GatewaySimulationTurnProvider:
    """Call one selected SDK provider without re-entering governed execution."""

    def __init__(
        self,
        *,
        db_session: Any,
        preferred_provider: str | None,
        model: str | None,
        allowed_provider_types: set[str] | None = None,
        allowed_models: set[str] | None = None,
    ) -> None:
        from backend.llm_gateway.gateway import LLMGateway

        self._gateway = LLMGateway(db_session=db_session)
        self._preferred_provider = preferred_provider
        self._requested_model = model
        self._allowed_provider_types = set(allowed_provider_types or set())
        self._allowed_models = set(allowed_models or set())
        self._sdk_provider: Any = None
        self._provider_record: Any = None
        self.provider_type = "unresolved"
        self.model = str(model or "unresolved")
        self.pricing_status = "unknown"

    async def _resolve(self) -> None:
        if self._sdk_provider is not None:
            return
        from backend.llm_gateway.provider_manifest import default_model_for_provider

        candidates = await self._gateway._get_eligible_providers(
            preferred_name=self._preferred_provider,
            allowed_provider_types=self._allowed_provider_types or None,
            allowed_models=(
                {self._requested_model}
                if self._requested_model
                else (self._allowed_models or None)
            ),
        )
        if not candidates:
            raise RuntimeError("SIMULATION_PROVIDER_UNAVAILABLE")
        self._provider_record = candidates[0]
        self.provider_type = str(self._provider_record.provider_type)
        self.model = str(
            self._requested_model
            or getattr(self._provider_record, "model_id", None)
            or default_model_for_provider(self.provider_type)
        )
        self._sdk_provider = self._gateway._create_sdk_provider(self._provider_record)

    async def preflight(self) -> None:
        await self._resolve()

    def estimate_max_cost_usd(self, max_total_tokens: int) -> float | None:
        from backend.llm_gateway.governance import AIGovernanceEngine

        input_only = AIGovernanceEngine.estimate_cost_usd(
            self.model,
            max_total_tokens,
            0,
        )
        output_only = AIGovernanceEngine.estimate_cost_usd(
            self.model,
            0,
            max_total_tokens,
        )
        if input_only is None or output_only is None:
            self.pricing_status = "unknown"
            return None
        self.pricing_status = "available"
        return round(max(input_only, output_only), 8)

    async def generate_turn(
        self,
        *,
        prompt: str,
        persona: str,
        max_tokens: int,
        simulation_id: str,
    ) -> dict[str, Any]:
        await self._resolve()
        response = await self._sdk_provider.complete(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are participating in a bounded simulation as "
                        f"{persona}. State assumptions and do not invent evidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            model=self.model,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        usage = response.usage or {}
        tokens_in = int(usage.get("prompt_tokens") or 0)
        tokens_out = int(usage.get("completion_tokens") or 0)
        from backend.llm_gateway.governance import AIGovernanceEngine

        estimated_cost = AIGovernanceEngine.estimate_cost_usd(
            response.model or self.model,
            tokens_in,
            tokens_out,
        )
        return {
            "content": response.text,
            "provider": self.provider_type,
            "model": response.model or self.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "estimated_cost_usd": estimated_cost,
        }

    async def close(self) -> None:
        if self._sdk_provider is not None:
            await self._sdk_provider.close()
