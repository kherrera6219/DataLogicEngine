"""Current provider model defaults for LLM gateway configuration."""

OPENAI_LATEST_MODEL = "gpt-5.5"
ANTHROPIC_LATEST_MODEL = "claude-opus-4-7"
GOOGLE_LATEST_MODEL = "gemini-3.5-flash"

# ── Local provider tier model map ─────────────────────────────────────────────
# All local tiers route through a single Ollama LLMProvider record.
# The escalation engine selects the model string per tier; Ollama loads it
# on demand. Cloud tiers (4–5) use separate LLMProvider records with credentials.
#
# Tier 0 — ultra-light, fast turnaround (trivial queries / quick lookups)
OLLAMA_TIER0_MODEL = "gemma4:e4b"
# Tier 1 — DataLogicEngine primary (structured reasoning, data queries)
OLLAMA_TIER1_MODEL = "gemma4:12b"
# Tier 2 — medium coding / complex analysis
OLLAMA_TIER2_MODEL = "qwen3:14b"
# Tier 3 — heavy agentic coding tasks
OLLAMA_TIER3_MODEL = "devstral-small-2"
# Tier 4 — cloud fast (internet required)
CLOUD_TIER4_MODEL = "gemini-3.5-flash"
# Tier 5 — cloud full / hardest questions (internet required)
CLOUD_TIER5_MODEL = "gpt-5.5"

# Default used when a new Ollama provider record is created with no explicit model.
OLLAMA_DEFAULT_MODEL = OLLAMA_TIER1_MODEL

# Convenience alias kept for code that predated the tier naming.
OLLAMA_LIGHT_MODEL = OLLAMA_TIER0_MODEL
OLLAMA_PRIMARY_MODEL = OLLAMA_TIER1_MODEL

# Standardized on a single OpenAI model: gpt-5.5 is the only OpenAI model used.
OPENAI_PRO_MODEL = "gpt-5.5"
OPENAI_STANDARD_MODEL = "gpt-5.5"
OPENAI_FAST_MODEL = "gpt-5.5"
OPENAI_NANO_MODEL = "gpt-5.5"
OPENAI_LONG_CONTEXT_MODEL = "gpt-5.5"
OPENAI_RESEARCH_MODEL = "gpt-5.5"

GOOGLE_PRIMARY_MODEL = GOOGLE_LATEST_MODEL
GOOGLE_FAST_MODEL = "gemini-3-flash-preview"

ANTHROPIC_PRIMARY_MODEL = ANTHROPIC_LATEST_MODEL

DEFAULT_MODEL_BY_PROVIDER = {
    "openai": OPENAI_LATEST_MODEL,
    "azure": OPENAI_LATEST_MODEL,
    "anthropic": ANTHROPIC_LATEST_MODEL,
    "google": GOOGLE_LATEST_MODEL,
    "gemini": GOOGLE_LATEST_MODEL,
    # Local inference providers — all default to the primary Ollama model.
    "ollama": OLLAMA_DEFAULT_MODEL,
    "local_slm": OLLAMA_DEFAULT_MODEL,
    "vllm": OLLAMA_DEFAULT_MODEL,
}


def default_model_for_provider(provider_type: str | None) -> str:
    """Return the current default model for a provider type."""
    normalized = str(provider_type or "openai").strip().lower()
    return DEFAULT_MODEL_BY_PROVIDER.get(normalized, OPENAI_LATEST_MODEL)
