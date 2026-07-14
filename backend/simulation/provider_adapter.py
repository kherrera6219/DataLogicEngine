"""Hard-budget provider adapter for simulation turns only.

The adapter deliberately exposes no ``process`` or ``execute`` method, so a
debate turn cannot recursively enter the complete governed request pipeline.
"""

from __future__ import annotations

import inspect
import time
from collections.abc import Callable
from typing import Any


class BoundedSimulationProviderAdapter:
    """Expose one bounded simulation-turn method over a provider-only client."""

    def __init__(
        self,
        *,
        provider: Any,
        simulation_id: str,
        max_provider_calls: int,
        max_total_tokens: int,
        initial_provider_calls: int = 0,
        initial_tokens_in: int = 0,
        initial_tokens_out: int = 0,
        initial_estimated_cost_usd: float = 0.0,
        initial_pricing_status: str = "available",
        max_cost_usd: float | None = None,
        deadline_monotonic: float | None = None,
        is_cancel_requested: Callable[[], bool] | None = None,
        is_pause_requested: Callable[[], bool] | None = None,
        on_call_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if provider is None or not callable(getattr(provider, "generate_turn", None)):
            raise ValueError("Simulation provider must expose generate_turn only")
        if max_provider_calls < 1 or max_total_tokens < 1:
            raise ValueError("Simulation provider budgets must be positive")
        self._provider = provider
        self.simulation_id = str(simulation_id)
        self.max_provider_calls = int(max_provider_calls)
        self.max_total_tokens = int(max_total_tokens)
        self.max_cost_usd = None if max_cost_usd is None else max(0.0, float(max_cost_usd))
        self.deadline_monotonic = deadline_monotonic
        self._is_cancel_requested = is_cancel_requested or (lambda: False)
        self._is_pause_requested = is_pause_requested or (lambda: False)
        self._on_call_event = on_call_event
        self.provider_calls_used = max(0, int(initial_provider_calls))
        self.tokens_in = max(0, int(initial_tokens_in))
        self.tokens_out = max(0, int(initial_tokens_out))
        self.estimated_cost_usd = max(0.0, float(initial_estimated_cost_usd))
        self.pricing_status = str(initial_pricing_status or "unknown")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, (len(text) + 3) // 4)

    def _preflight(self, *, prompt: str, max_tokens: int) -> None:
        if self._is_cancel_requested():
            raise RuntimeError("SIMULATION_CANCELLED")
        if self._is_pause_requested():
            raise RuntimeError("SIMULATION_PAUSED")
        if self.deadline_monotonic is not None and time.monotonic() >= self.deadline_monotonic:
            raise RuntimeError("SIMULATION_DEADLINE_EXCEEDED")
        if self.provider_calls_used >= self.max_provider_calls:
            raise RuntimeError("SIMULATION_PROVIDER_CALL_BUDGET_EXHAUSTED")
        estimated_total = self.tokens_in + self.tokens_out + self._estimate_tokens(prompt) + max_tokens
        if estimated_total > self.max_total_tokens:
            raise RuntimeError("SIMULATION_TOKEN_BUDGET_EXHAUSTED")
        if self.max_cost_usd is not None and self.estimated_cost_usd >= self.max_cost_usd:
            raise RuntimeError("SIMULATION_COST_BUDGET_EXHAUSTED")

    async def generate_simulation_turn(
        self, *, prompt: str, persona: str, max_tokens: int
    ) -> str:
        prompt = str(prompt or "")
        persona = str(persona or "").strip()
        max_tokens = max(1, int(max_tokens))
        self._preflight(prompt=prompt, max_tokens=max_tokens)
        self.provider_calls_used += 1
        call_index = self.provider_calls_used
        provider_type = str(getattr(self._provider, "provider_type", "unknown"))
        model = str(getattr(self._provider, "model", "unknown"))
        started_at = time.monotonic()
        self._publish_call_event(
            {
                "event": "started",
                "call_index": call_index,
                "persona": persona,
                "provider_type": provider_type,
                "model": model,
            }
        )

        try:
            result = self._provider.generate_turn(
                prompt=prompt,
                persona=persona,
                max_tokens=max_tokens,
                simulation_id=self.simulation_id,
            )
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            self._publish_call_event(
                {
                    "event": "failed",
                    "call_index": call_index,
                    "persona": persona,
                    "provider_type": provider_type,
                    "model": model,
                    "latency_ms": int((time.monotonic() - started_at) * 1000),
                    "error_code": type(exc).__name__[:100],
                }
            )
            raise

        if isinstance(result, dict):
            content = str(result.get("content") or "")
            tokens_in = max(0, int(result.get("tokens_in") or self._estimate_tokens(prompt)))
            tokens_out = max(0, int(result.get("tokens_out") or self._estimate_tokens(content)))
            estimated_cost = result.get("estimated_cost_usd")
            provider_type = str(result.get("provider") or provider_type)
            model = str(result.get("model") or model)
            if estimated_cost is None:
                self.pricing_status = "unknown"
            else:
                self.estimated_cost_usd += max(0.0, float(estimated_cost))
        else:
            content = str(result or "")
            tokens_in = self._estimate_tokens(prompt)
            tokens_out = self._estimate_tokens(content)
            self.pricing_status = "unknown"

        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        if self.max_cost_usd is not None and self.estimated_cost_usd > self.max_cost_usd:
            self._raise_post_call_failure(
                "SIMULATION_COST_BUDGET_EXHAUSTED",
                call_index=call_index,
                persona=persona,
                provider_type=provider_type,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                started_at=started_at,
            )
        if self.tokens_in + self.tokens_out > self.max_total_tokens:
            self._raise_post_call_failure(
                "SIMULATION_TOKEN_BUDGET_EXHAUSTED",
                call_index=call_index,
                persona=persona,
                provider_type=provider_type,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                started_at=started_at,
            )
        if not content.strip():
            self._raise_post_call_failure(
                "SIMULATION_PROVIDER_EMPTY_RESPONSE",
                call_index=call_index,
                persona=persona,
                provider_type=provider_type,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                started_at=started_at,
            )
        self._publish_call_event(
            {
                "event": "completed",
                "call_index": call_index,
                "persona": persona,
                "provider_type": provider_type,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "estimated_cost_usd": estimated_cost if isinstance(result, dict) else None,
                "pricing_status": self.pricing_status,
                "latency_ms": int((time.monotonic() - started_at) * 1000),
            }
        )
        return content

    def _publish_call_event(self, payload: dict[str, Any]) -> None:
        if self._on_call_event is not None:
            self._on_call_event(dict(payload))

    def _raise_post_call_failure(
        self,
        code: str,
        *,
        call_index: int,
        persona: str,
        provider_type: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        started_at: float,
    ) -> None:
        self._publish_call_event(
            {
                "event": "failed",
                "call_index": call_index,
                "persona": persona,
                "provider_type": provider_type,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "pricing_status": self.pricing_status,
                "latency_ms": int((time.monotonic() - started_at) * 1000),
                "error_code": code,
            }
        )
        raise RuntimeError(code)

    def usage_snapshot(self) -> dict[str, Any]:
        return {
            "provider_calls_used": self.provider_calls_used,
            "max_provider_calls": self.max_provider_calls,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "max_total_tokens": self.max_total_tokens,
            "estimated_cost_usd": (
                round(self.estimated_cost_usd, 8)
                if self.pricing_status == "available"
                else None
            ),
            "pricing_status": self.pricing_status,
            "max_cost_usd": self.max_cost_usd,
        }
