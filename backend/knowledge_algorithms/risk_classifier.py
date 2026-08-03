"""
KA risk tier classifier.

Assigns each Knowledge Algorithm a risk tier so the frontend can
gate destructive operations behind a confirmation dialog.

Tiers
------
read_only   — Returns data only; no side-effects.
write       — Persists or modifies data.
destructive — Deletes, overwrites, or irreversibly transforms data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskTier(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True)
class KARiskProfile:
    ka_id: str
    tier: RiskTier
    reason: str
    requires_confirmation: bool

    @property
    def label(self) -> str:
        return {
            RiskTier.READ_ONLY: "Read-only",
            RiskTier.WRITE: "Write",
            RiskTier.DESTRUCTIVE: "Destructive",
        }[self.tier]


# Explicit overrides for KAs with non-obvious risk.
# Everything not listed defaults to READ_ONLY.
_OVERRIDES: dict[str, tuple[RiskTier, str]] = {
    # Write-tier KAs (create/update side-effects)
    "KA-010": (RiskTier.WRITE, "Creates knowledge-graph nodes"),
    "KA-011": (RiskTier.WRITE, "Creates or updates knowledge edges"),
    "KA-012": (RiskTier.WRITE, "Updates node metadata"),
    "KA-020": (RiskTier.WRITE, "Persists simulation state"),
    "KA-030": (RiskTier.WRITE, "Writes audit evidence records"),
    "KA-031": (RiskTier.WRITE, "Updates compliance records"),
    "KA-050": (RiskTier.WRITE, "Stores model routing policy"),
    "KA-060": (RiskTier.WRITE, "Persists external API credentials"),
    "KA-100": (RiskTier.WRITE, "Records truth consensus result"),
    # Destructive-tier KAs
    "KA-013": (RiskTier.DESTRUCTIVE, "Deletes knowledge-graph nodes and their edges"),
    "KA-014": (RiskTier.DESTRUCTIVE, "Bulk-removes knowledge edges"),
    "KA-021": (RiskTier.DESTRUCTIVE, "Purges simulation session data"),
    "KA-061": (RiskTier.DESTRUCTIVE, "Blocks and discards the current query pipeline"),
    "KA-080": (RiskTier.DESTRUCTIVE, "Overwrites model routing policy"),
    "KA-113": (RiskTier.DESTRUCTIVE, "Routes to Tier-4 refinement, discarding lower-tier output"),
}


def classify(ka_id: str) -> KARiskProfile:
    """Return the risk profile for the given KA identifier."""
    ka_upper = ka_id.upper()
    if ka_upper in _OVERRIDES:
        tier, reason = _OVERRIDES[ka_upper]
    else:
        tier = RiskTier.READ_ONLY
        reason = "Returns analysis or recommendations only"

    return KARiskProfile(
        ka_id=ka_upper,
        tier=tier,
        reason=reason,
        requires_confirmation=tier in (RiskTier.WRITE, RiskTier.DESTRUCTIVE),
    )


def classify_many(ka_ids: list[str]) -> list[KARiskProfile]:
    return [classify(ka_id) for ka_id in ka_ids]


def highest_tier(ka_ids: list[str]) -> Optional[RiskTier]:
    """Return the most severe risk tier across a list of KA identifiers."""
    profiles = classify_many(ka_ids)
    if not profiles:
        return None
    order = [RiskTier.READ_ONLY, RiskTier.WRITE, RiskTier.DESTRUCTIVE]
    return max((p.tier for p in profiles), key=lambda t: order.index(t))
