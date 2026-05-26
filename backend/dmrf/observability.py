"""Lightweight DMRF observability state."""

from __future__ import annotations

from collections import Counter
from typing import Any


class DMRFObservability:
    """In-process metrics used by API/IPC status surfaces."""

    def __init__(self):
        self.tier_counter: Counter[str] = Counter()
        self.last_status: dict[str, Any] = {"status": "idle"}

    def record(self, *, tier: str, frost_depth: int, run_id: str) -> None:
        self.tier_counter[tier] += 1
        self.last_status = {
            "status": "ok",
            "tier": tier,
            "frost_depth": frost_depth,
            "run_id": run_id,
            "tier_counts": dict(self.tier_counter),
        }

    def status(self) -> dict[str, Any]:
        return dict(self.last_status)

    def prometheus_lines(self, prefix: str = "datalogicengine") -> list[str]:
        """Render low-cardinality DMRF metrics."""
        lines = [
            f"# HELP {prefix}_dmrf_router_tier_total DMRF requests classified by tier.",
            f"# TYPE {prefix}_dmrf_router_tier_total counter",
        ]
        for tier, count in sorted(self.tier_counter.items()):
            safe_tier = tier.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{prefix}_dmrf_router_tier_total{{tier="{safe_tier}"}} {count}')

        status = self.status()
        frost_depth = status.get("frost_depth")
        lines.extend(
            [
                f"# HELP {prefix}_dmrf_frost_depth Last DMRF FROST depth.",
                f"# TYPE {prefix}_dmrf_frost_depth gauge",
                f"{prefix}_dmrf_frost_depth {int(frost_depth or 0)}",
            ]
        )
        return lines
