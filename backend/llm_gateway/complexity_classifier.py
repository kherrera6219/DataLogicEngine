"""
Heuristic query complexity classifier for the 6-tier escalation engine.

Classifies queries into tiers 0–5 based on structural signals — no external
model call is made.  Runs synchronously on every gateway request and must stay
cheap (< 1 ms for typical inputs).

Tier map (matches escalation_config.TIER_CHAIN; authoritative model
strings live in model_defaults.py):
  0 — ultra-light    gemma4:latest        trivial Q&A / single-word lookups
  1 — primary        gemma4:12b           standard chat, structured data queries
  2 — medium         qwen3:14b            analysis, light coding, multi-step
  3 — heavy-local    devstral-small-2     agentic / complex system coding
  4 — cloud-fast     gemini-3.5-flash     cloud (auto-cap disabled by default)
  5 — cloud-full     gpt-5.5              cloud (auto-cap disabled by default)

Cloud tiers (4–5) are returned only when ``allow_cloud_escalation=True`` is
passed.  The default cap is Tier 3 so the app stays fully local until the user
explicitly enables cloud escalation via the Sprint 6c policy settings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationResult:
    tier: int          # 0–5
    reason: str        # human-readable diagnostic (shown in logs + UI)
    score: float       # 0.0–1.0 normalised (informational only)


# ---------------------------------------------------------------------------
# Signal tables
# ---------------------------------------------------------------------------

# Patterns that pull the result DOWN to Tier 0 (trivial) when matched.
_TRIVIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(hi|hello|hey|thanks|thank you|ok|yes|no|sure|cool)[!?.]*\s*$", re.I),
    re.compile(r"^(what|who|when|where|is|are|can|could)\s+(is|are|a|an|the)\s+\w+[?]?\s*$", re.I),
    re.compile(r"^\w{1,30}[?.!]?\s*$"),   # single word or very short phrase
]

# Patterns that boost toward Tier 2 (code / analysis).
# Two or more hits → Tier 2 minimum.  One hit → Tier 1 minimum.
_CODE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"```"),
    re.compile(r"\bdef\b|\bfunction\b|\bclass\b|\bimport\b|\bexport\b", re.I),
    re.compile(r"\.(py|js|ts|go|java|cpp|rs|rb|sh|sql)\b", re.I),
    re.compile(r"\b(async|await|promise|coroutine|thread|mutex)\b", re.I),
    re.compile(r"\b(sql|query|database|schema|migration|orm)\b", re.I),
    re.compile(r"\b(api|endpoint|rest|graphql|webhook|http|curl)\b", re.I),
    re.compile(r"\b(debug|error|exception|traceback|stack.?trace|segfault)\b", re.I),
    re.compile(r"\b(implement|refactor|optimize|algorithm|complexity)\b", re.I),
    re.compile(r"\b(json|yaml|xml|csv|regex|parser)\b", re.I),
    re.compile(r"\b(docker|kubernetes|container|deployment|ci.?cd)\b", re.I),
]

# Patterns that boost toward Tier 3 (heavy-local / agentic).
# One or more hits → Tier 3 minimum.
_AGENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(build|create|write|design|architect)\s+(a|an|the)?\s*(full|complete|entire|production)", re.I),
    re.compile(r"\b(multi.?step|pipeline|workflow|orchestrat)", re.I),
    re.compile(r"\b(agentic?|autonomous|self.?hosted|end.?to.?end)\b", re.I),
    re.compile(r"multiple\s+(files|modules|classes|services|microservices|components)", re.I),
    re.compile(r"\bstep.?by.?step\s+(guide|tutorial|implementation|walkthrough)\b", re.I),
    re.compile(r"\b(comprehensive|exhaustive|thorough)\s+(analysis|review|audit|report|breakdown)\b", re.I),
    re.compile(r"\bwrite\s+(a\s+)?(full|complete|production).?(app|application|system|service)\b", re.I),
]

# Patterns that hint at cloud tier (informational — stored in meta, not used
# to auto-escalate without explicit policy enable).
_CLOUD_HINT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(latest|current|today|yesterday|recent|real.?time|live)\b", re.I),
    re.compile(r"\b(news|trending|announcement|press.?release)\b", re.I),
    re.compile(r"\b(2025|2026|2027)\b"),
    re.compile(r"compare\b.{0,60}\bversus\b|\bversus\b.{0,60}\bcompare\b", re.I),
]

# Maximum tier returned without ``allow_cloud_escalation=True``.
_LOCAL_TIER_CAP = 3


class ComplexityClassifier:
    """
    Classify a single query string into a provider tier (0–5).

    The classifier is stateless and safe to share across requests.
    """

    def classify(
        self,
        query: str,
        *,
        allow_cloud_escalation: bool = False,
    ) -> ClassificationResult:
        """
        Return a ``ClassificationResult`` for *query*.

        Parameters
        ----------
        query:
            The raw user query string.
        allow_cloud_escalation:
            When False (default) the returned tier is capped at 3 (local-heavy)
            so the app never auto-escalates to cloud providers.
        """
        text = query.strip()
        if not text:
            return ClassificationResult(tier=0, reason="empty query", score=0.0)

        word_count = len(text.split())
        char_count = len(text)

        # ── 1. Length-based baseline ───────────────────────────────────────
        if char_count < 25 or word_count < 4:
            base_tier = 0
        elif char_count < 150 or word_count < 25:
            base_tier = 1
        elif char_count < 450 or word_count < 90:
            base_tier = 2
        else:
            base_tier = 3

        tier = base_tier
        reason = f"length(chars={char_count},words={word_count})"

        # ── 2. Trivial override (beats everything) ─────────────────────────
        if base_tier <= 1 and any(p.search(text) for p in _TRIVIAL_PATTERNS):
            return ClassificationResult(tier=0, reason="trivial-pattern", score=0.0)

        # ── 3. Code/analysis signal boost → min Tier 2 ───────────────────
        # Any coding keyword signals coding intent; use at least Tier 2.
        # Trivial-pattern override at step 2 already filtered out simple
        # lookups like "what is SQL?" so this boost is safe.
        code_hits = sum(1 for p in _CODE_PATTERNS if p.search(text))
        if code_hits >= 1:
            if tier < 2:
                tier = 2
                reason = f"code-signals({code_hits})"

        # ── 4. Agent/heavy boost → min Tier 3 ────────────────────────────
        agent_hits = sum(1 for p in _AGENT_PATTERNS if p.search(text))
        if agent_hits >= 1 and tier < 3:
            tier = 3
            reason = f"agent-signals({agent_hits})"

        # ── 5. Cloud hint (stored in meta; does not raise tier past cap) ──
        cloud_hint = any(p.search(text) for p in _CLOUD_HINT_PATTERNS)

        # ── 6. Apply ceiling ──────────────────────────────────────────────
        cap = 5 if allow_cloud_escalation else _LOCAL_TIER_CAP
        tier = min(tier, cap)

        if cloud_hint and tier >= _LOCAL_TIER_CAP and not allow_cloud_escalation:
            reason += "+cloud-hint(capped-T3)"

        return ClassificationResult(tier=tier, reason=reason, score=round(tier / 5.0, 2))
