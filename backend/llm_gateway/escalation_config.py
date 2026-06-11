"""
6-tier provider escalation chain for DataLogicEngine.

All local tiers (0–3) are routed through a single Ollama LLMProvider DB
record; only the model string changes per tier.  Cloud tiers (4–5) use
separate LLMProvider records that carry their own credentials.

Tier  Provider  Model                    Label            Cloud?
───────────────────────────────────────────────────────────────────
  0   ollama    gemma4:latest            T0·local-light   no
  1   ollama    gemma4:12b               T1·local-primary no
  2   ollama    qwen3:14b                T2·local-medium  no
  3   ollama    devstral-small-2:latest  T3·local-heavy   no
  4   google    gemini-3.5-flash         T4·cloud-fast    yes
  5   openai    gpt-5.5                  T5·cloud-full    yes

The authoritative model strings live in model_defaults.py; this table is
documentation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.llm_gateway.model_defaults import (
    CLOUD_TIER4_MODEL,
    CLOUD_TIER5_MODEL,
    OLLAMA_TIER0_MODEL,
    OLLAMA_TIER1_MODEL,
    OLLAMA_TIER2_MODEL,
    OLLAMA_TIER3_MODEL,
)


@dataclass(frozen=True)
class TierConfig:
    tier: int
    provider_type: str   # matches LLMProvider.provider_type in DB
    model: str
    label: str           # shown in the UI badge
    is_cloud: bool


TIER_CHAIN: tuple[TierConfig, ...] = (
    TierConfig(0, "ollama", OLLAMA_TIER0_MODEL, "T0·local-light",   is_cloud=False),
    TierConfig(1, "ollama", OLLAMA_TIER1_MODEL, "T1·local-primary", is_cloud=False),
    TierConfig(2, "ollama", OLLAMA_TIER2_MODEL, "T2·local-medium",  is_cloud=False),
    TierConfig(3, "ollama", OLLAMA_TIER3_MODEL, "T3·local-heavy",   is_cloud=False),
    TierConfig(4, "google", CLOUD_TIER4_MODEL,  "T4·cloud-fast",    is_cloud=True),
    TierConfig(5, "openai", CLOUD_TIER5_MODEL,  "T5·cloud-full",    is_cloud=True),
)

_BY_TIER: dict[int, TierConfig] = {tc.tier: tc for tc in TIER_CHAIN}

# Provider types served locally via Ollama (single DB record, model-per-tier).
LOCAL_PROVIDER_TYPES: frozenset[str] = frozenset(
    tc.provider_type for tc in TIER_CHAIN if not tc.is_cloud
)


def get_tier_config(tier: int) -> Optional[TierConfig]:
    """Return the TierConfig for *tier*, or None if out of range."""
    return _BY_TIER.get(tier)


def tier_for_model(model: str) -> Optional[TierConfig]:
    """Reverse-lookup: find the first tier whose model matches *model*."""
    for tc in TIER_CHAIN:
        if tc.model == model:
            return tc
    return None
