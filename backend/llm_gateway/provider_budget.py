"""Server-enforced provider call and token ceilings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import Any

from sqlalchemy import case, func


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    allowed: bool
    code: str
    message: str
    usage: dict[str, int | float | None]
    limits: dict[str, int | float | None]
    warning_threshold_crossed: bool = False


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _env_optional_float(name: str) -> float | None:
    raw = str(os.environ.get(name, "") or "").strip()
    if not raw:
        return None
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


class ProviderBudgetPolicy:
    """Evaluate durable call/token ceilings before every provider attempt."""

    def __init__(self, db_session: Any = None) -> None:
        self.db = db_session

    @staticmethod
    def request_call_limit(mode: Any, constraints: dict[str, Any]) -> int:
        server_limit = 2 if str(getattr(mode, "value", mode)) == "enhanced" else 1
        requested = constraints.get("max_provider_calls")
        try:
            requested_limit = int(requested)
        except (TypeError, ValueError):
            requested_limit = server_limit
        return max(1, min(server_limit, requested_limit))

    @classmethod
    def configured_limits(
        cls,
        mode: Any = "standard",
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, int | float | None]:
        """Return the server-owned limits that the UI may display but not raise."""
        return {
            "request_calls": cls.request_call_limit(mode, constraints or {}),
            "session_calls": _env_int("AI_PROVIDER_CALLS_PER_SESSION", 100),
            "daily_calls": _env_int("AI_PROVIDER_CALLS_PER_DAY", 500),
            "monthly_calls": _env_int("AI_PROVIDER_CALLS_PER_MONTH", 5000),
            "daily_tokens": _env_int("AI_PROVIDER_TOKENS_PER_DAY", 2_000_000),
            "monthly_tokens": _env_int("AI_PROVIDER_TOKENS_PER_MONTH", 20_000_000),
            "monthly_spend_usd": _env_optional_float("AI_PROVIDER_SPEND_USD_PER_MONTH"),
        }

    def evaluate(
        self,
        *,
        context: Any,
        projected_input_tokens: int,
        projected_output_tokens: int,
        projected_cost_usd: float | None = None,
    ) -> BudgetDecision:
        request = context.request
        limits = self.configured_limits(request.mode, request.constraints)
        usage: dict[str, int | float | None] = {
            "request_calls": int(context.provider_call_count),
            "session_calls": 0,
            "daily_calls": 0,
            "monthly_calls": 0,
            "daily_tokens": 0,
            "monthly_tokens": 0,
            "monthly_spend_usd": None,
            "monthly_unknown_price_calls": 0,
        }

        if self.db is not None:
            try:
                from models import LLMProviderUsage

                now = datetime.now(UTC)
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                month_start = day_start.replace(day=1)

                def aggregate(
                    start: datetime | None,
                    session_id: str | None = None,
                ) -> tuple[int, int, float, int]:
                    query = self.db.query(
                        func.count(LLMProviderUsage.id),
                        func.coalesce(func.sum(LLMProviderUsage.tokens_in + LLMProviderUsage.tokens_out), 0),
                        func.coalesce(func.sum(LLMProviderUsage.estimated_cost_usd), 0.0),
                        func.coalesce(
                            func.sum(
                                case(
                                    (LLMProviderUsage.estimated_cost_usd.is_(None), 1),
                                    else_=0,
                                )
                            ),
                            0,
                        ),
                    )
                    if start is not None:
                        query = query.filter(LLMProviderUsage.created_at >= start)
                    if request.user_id is not None:
                        query = query.filter(LLMProviderUsage.user_id == request.user_id)
                    if session_id:
                        query = query.filter(LLMProviderUsage.session_id == str(session_id))
                    row = query.one()
                    return (
                        int(row[0] or 0),
                        int(row[1] or 0),
                        float(row[2] or 0.0),
                        int(row[3] or 0),
                    )

                daily_calls, daily_tokens, _, _ = aggregate(day_start)
                monthly_calls, monthly_tokens, monthly_spend, unknown_price_calls = aggregate(month_start)
                usage["daily_calls"], usage["daily_tokens"] = daily_calls, daily_tokens
                usage["monthly_calls"], usage["monthly_tokens"] = monthly_calls, monthly_tokens
                usage["monthly_spend_usd"] = monthly_spend
                usage["monthly_unknown_price_calls"] = unknown_price_calls
                if request.session_id:
                    usage["session_calls"], _, _, _ = aggregate(
                        None, str(request.session_id)
                    )
            except Exception:
                # A ledger query failure cannot be represented as unused budget.
                return BudgetDecision(False, "BUDGET_LEDGER_UNAVAILABLE", "Provider usage ledger unavailable", usage, limits)

        projected_tokens = max(0, projected_input_tokens) + max(0, projected_output_tokens)
        checks = (
            ("request_calls", 1),
            ("session_calls", 1),
            ("daily_calls", 1),
            ("monthly_calls", 1),
            ("daily_tokens", projected_tokens),
            ("monthly_tokens", projected_tokens),
        )
        for key, increment in checks:
            if int(usage[key] or 0) + increment > int(limits[key] or 0):
                return BudgetDecision(False, f"{key.upper()}_HARD_LIMIT", f"Provider {key.replace('_', ' ')} limit exceeded", usage, limits)

        spend_limit = limits.get("monthly_spend_usd")
        if spend_limit is not None and projected_cost_usd is not None:
            monthly_spend = float(usage.get("monthly_spend_usd") or 0.0)
            if monthly_spend + max(0.0, projected_cost_usd) > float(spend_limit):
                return BudgetDecision(
                    False,
                    "MONTHLY_SPEND_USD_HARD_LIMIT",
                    "Provider monthly estimated spend limit exceeded",
                    usage,
                    limits,
                )

        # Selecting enhanced mode explicitly authorizes its bounded second call;
        # warnings apply to durable session/day/month ceilings.
        warning_checks = tuple(item for item in checks if item[0] != "request_calls")
        ratios = [
            (int(usage[key] or 0) + increment) / max(1, int(limits[key] or 1))
            for key, increment in warning_checks
        ]
        if spend_limit is not None and projected_cost_usd is not None:
            ratios.append(
                (float(usage.get("monthly_spend_usd") or 0.0) + max(0.0, projected_cost_usd))
                / max(0.01, float(spend_limit))
            )
        warning = max(ratios, default=0.0) >= 0.8
        confirmed = bool(request.metadata.get("budget_warning_confirmed"))
        if warning and not confirmed:
            return BudgetDecision(False, "BUDGET_WARNING_CONFIRMATION_REQUIRED", "Provider usage warning threshold requires confirmation", usage, limits, True)
        return BudgetDecision(True, "BUDGET_OK", "Provider budget available", usage, limits, warning)
