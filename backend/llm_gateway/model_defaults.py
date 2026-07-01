"""Current provider model defaults for LLM gateway configuration.

Cloud-only: the app uses one user-selected cloud model — OpenAI ``gpt-5.5`` or
Google ``gemini-3.5-flash``. There is no local/Ollama tier chain.
"""

OPENAI_LATEST_MODEL = "gpt-5.5"
ANTHROPIC_LATEST_MODEL = "claude-opus-4-7"
GOOGLE_LATEST_MODEL = "gemini-3.1-pro-preview"

# Standardized on a single OpenAI model: gpt-5.5 is the only OpenAI model used.
OPENAI_PRO_MODEL = "gpt-5.5"
OPENAI_STANDARD_MODEL = "gpt-5.5"
OPENAI_FAST_MODEL = "gpt-5.5"
OPENAI_NANO_MODEL = "gpt-5.5"
OPENAI_LONG_CONTEXT_MODEL = "gpt-5.5"
OPENAI_RESEARCH_MODEL = "gpt-5.5"

GOOGLE_PRIMARY_MODEL = GOOGLE_LATEST_MODEL
GOOGLE_FAST_MODEL = GOOGLE_LATEST_MODEL

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
