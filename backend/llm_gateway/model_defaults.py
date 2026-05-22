"""Current provider model defaults for LLM gateway configuration."""

OPENAI_LATEST_MODEL = "gpt-5.5"
ANTHROPIC_LATEST_MODEL = "claude-opus-4-7"
GOOGLE_LATEST_MODEL = "gemini-3.5-flash"

OPENAI_PRO_MODEL = "gpt-5.5"
OPENAI_STANDARD_MODEL = "gpt-5.5"
OPENAI_FAST_MODEL = "gpt-5.4-mini"
OPENAI_NANO_MODEL = "gpt-5.4-nano"
OPENAI_LONG_CONTEXT_MODEL = "gpt-5.5"
OPENAI_RESEARCH_MODEL = "o3-deep-research"

GOOGLE_PRIMARY_MODEL = GOOGLE_LATEST_MODEL
GOOGLE_FAST_MODEL = "gemini-3-flash-preview"

ANTHROPIC_PRIMARY_MODEL = ANTHROPIC_LATEST_MODEL

DEFAULT_MODEL_BY_PROVIDER = {
    "openai": OPENAI_LATEST_MODEL,
    "azure": OPENAI_LATEST_MODEL,
    "anthropic": ANTHROPIC_LATEST_MODEL,
    "google": GOOGLE_LATEST_MODEL,
    "gemini": GOOGLE_LATEST_MODEL,
}


def default_model_for_provider(provider_type: str | None) -> str:
    """Return the current default model for a provider type."""
    normalized = str(provider_type or "openai").strip().lower()
    return DEFAULT_MODEL_BY_PROVIDER.get(normalized, OPENAI_LATEST_MODEL)
