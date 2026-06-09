"""
LLM Tier Availability — startup probe and graceful cascade helper.

Probes Ollama at app startup to find which local model tiers (T0–T3)
have their weights pulled.  The result is cached module-wide so the
gateway's escalation block can query it cheaply on every request.

Cascade contract (local tiers only)
------------------------------------
When the classifier picks tier N but that model is not pulled, the
gateway should fall back DOWN to the highest available local tier
rather than failing.  A lower-capability response is always better
than a 500.  Cloud tiers (T4/T5) are never subject to this cascade —
their availability is controlled by the API-key gate.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level cache.  None = probe not yet run.
_available_local_tiers: Optional[frozenset[int]] = None

# Ensure the SDK is importable (mirrors the pattern in gateway.py).
_SDK_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "sdk" / "UKG_Python_SDK"
)


# ---------------------------------------------------------------------------
# Public read interface
# ---------------------------------------------------------------------------

def get_available_local_tiers() -> Optional[frozenset[int]]:
    """Return cached available local tier indices, or None if not yet probed."""
    return _available_local_tiers


def is_local_tier_available(tier: int) -> bool:
    """
    Return True if tier *tier* is known-available.

    Returns True when probe has not run yet (unknown → optimistic).
    """
    available = _available_local_tiers
    if available is None:
        return True  # optimistic until proven otherwise
    return tier in available


def find_best_available_tier(
    requested_tier: int,
    *,
    allow_cloud: bool = False,
) -> int:
    """
    Return the best viable tier index given current model availability.

    Rules
    -----
    1. If the probe has not run yet, return *requested_tier* unchanged
       (optimistic — let the gateway surface the error naturally).
    2. Cloud tiers (T4, T5): availability is controlled by the API-key
       gate, not model presence. Return as-is.
    3. Local tiers (T0–T3): if *requested_tier* is not available, walk
       DOWN to the highest available local tier.
    4. If no local tier is available and *allow_cloud* is True, return
       the lowest cloud tier (T4).
    5. If nothing viable exists, return *requested_tier* unchanged and
       let the gateway produce its normal error.
    """
    from backend.llm_gateway.escalation_config import TIER_CHAIN

    available = _available_local_tiers
    if available is None:
        return requested_tier  # not probed yet — optimistic pass-through

    cfg_map = {tc.tier: tc for tc in TIER_CHAIN}
    req_cfg = cfg_map.get(requested_tier)

    # Cloud tier: key-gate already handled by caller.
    if req_cfg is not None and req_cfg.is_cloud:
        return requested_tier

    # Local tier — already available.
    if requested_tier in available:
        return requested_tier

    # Cascade DOWN through available local tiers.
    for t in range(requested_tier - 1, -1, -1):
        cfg = cfg_map.get(t)
        if cfg is not None and not cfg.is_cloud and t in available:
            logger.info(
                "Tier cascade: T%d (%s) not pulled → using T%d (%s) instead",
                requested_tier,
                req_cfg.model if req_cfg else "?",
                t,
                cfg.model,
            )
            return t

    # No local tier available — escalate to cloud if allowed.
    if allow_cloud:
        cloud_tiers = sorted(
            tc.tier for tc in TIER_CHAIN if tc.is_cloud
        )
        if cloud_tiers:
            logger.info(
                "No local Ollama models available — routing to cloud tier T%d",
                cloud_tiers[0],
            )
            return cloud_tiers[0]

    # Nothing viable; return original and let gateway fail with a clear error.
    return requested_tier


# ---------------------------------------------------------------------------
# Startup probe
# ---------------------------------------------------------------------------

async def probe_local_tiers() -> frozenset[int]:
    """
    Query Ollama for installed models and cache which T0–T3 tiers are ready.

    Completely non-fatal: if Ollama is not running, all local tiers are
    marked unavailable and a startup warning is emitted.  Cloud tiers
    (T4/T5) are unaffected — their gate is the API-key check.

    Intended to be called once from a daemon background thread at startup.
    Returns the availability set so callers can await it directly.
    """
    global _available_local_tiers  # noqa: PLW0603

    from backend.llm_gateway.escalation_config import TIER_CHAIN

    local_tiers = [tc for tc in TIER_CHAIN if not tc.is_cloud]

    # --- Query Ollama --------------------------------------------------
    # Use the canonical OllamaClient (synchronous thin wrapper) rather than
    # OllamaProvider from the SDK, which deduplicates the /api/tags call.
    pulled_models: list[str] = []
    try:
        from backend.local_model_acceleration.ollama_client import OllamaClient

        pulled_models = OllamaClient().list_models()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Ollama startup probe could not reach Ollama: %s — "
            "local tiers (T0–T3) will be treated as unavailable.",
            exc,
        )

    # --- Match tier models against pulled list -------------------------
    def _is_available(model_name: str) -> bool:
        """Exact match, or base-name match (e.g. 'gemma4' matches 'gemma4:latest')."""
        base = model_name.split(":")[0]
        for p in pulled_models:
            if p == model_name or p.split(":")[0] == base:
                return True
        return False

    available: set[int] = set()
    rows: list[str] = []
    for tc in local_tiers:
        ok = _is_available(tc.model)
        if ok:
            available.add(tc.tier)
        pull_hint = f"  ← run: ollama pull {tc.model}" if not ok else ""
        symbol = "✓" if ok else "✗"
        rows.append(
            f"    T{tc.tier}  {symbol}  {tc.model:<34} {tc.label}{pull_hint}"
        )

    result = frozenset(available)
    _available_local_tiers = result

    # --- Emit startup summary -----------------------------------------
    sep = "─" * 72
    logger.info(
        "\n%s\nOllama local tier availability\n%s\n%s\n%s",
        sep, sep, "\n".join(rows), sep,
    )
    if not available:
        logger.warning(
            "No local Ollama models found.  "
            "Install Ollama from https://ollama.com then run:\n"
            "  ollama pull gemma4:latest\n"
            "  ollama pull gemma4:12b\n"
            "  ollama pull qwen3:14b\n"
            "  ollama pull devstral-small-2:latest\n"
            "Until then, only cloud tiers (T4/T5) will work if a key is saved."
        )
    elif len(available) < len(local_tiers):
        missing = [tc for tc in local_tiers if tc.tier not in available]
        logger.warning(
            "Partial Ollama model coverage: %d/%d local tiers available. "
            "Missing: %s.  Requests will cascade to available tiers.",
            len(available),
            len(local_tiers),
            ", ".join(f"T{tc.tier} ({tc.model})" for tc in missing),
        )

    return result
