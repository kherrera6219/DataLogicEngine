"""Compatibility exports derived from the canonical provider manifest."""

from backend.llm_gateway.provider_manifest import (
    DEFAULT_MODEL_BY_PROVIDER,
    SUPPORTED_PROVIDER_TYPES,
    default_model_for_provider,
)

__all__ = [
    "DEFAULT_MODEL_BY_PROVIDER",
    "SUPPORTED_PROVIDER_TYPES",
    "default_model_for_provider",
    "OPENAI_LATEST_MODEL",
    "GOOGLE_LATEST_MODEL",
    "OPENAI_PRO_MODEL",
    "OPENAI_STANDARD_MODEL",
    "OPENAI_FAST_MODEL",
    "OPENAI_NANO_MODEL",
    "OPENAI_LONG_CONTEXT_MODEL",
    "OPENAI_RESEARCH_MODEL",
    "GOOGLE_PRIMARY_MODEL",
    "GOOGLE_FAST_MODEL",
]


OPENAI_LATEST_MODEL = DEFAULT_MODEL_BY_PROVIDER["openai"]
GOOGLE_LATEST_MODEL = DEFAULT_MODEL_BY_PROVIDER["google"]

# Standardized on a single OpenAI model: gpt-5.5 is the only OpenAI model used.
OPENAI_PRO_MODEL = "gpt-5.5"
OPENAI_STANDARD_MODEL = "gpt-5.5"
OPENAI_FAST_MODEL = "gpt-5.5"
OPENAI_NANO_MODEL = "gpt-5.5"
OPENAI_LONG_CONTEXT_MODEL = "gpt-5.5"
OPENAI_RESEARCH_MODEL = "gpt-5.5"

GOOGLE_PRIMARY_MODEL = GOOGLE_LATEST_MODEL
GOOGLE_FAST_MODEL = GOOGLE_LATEST_MODEL
