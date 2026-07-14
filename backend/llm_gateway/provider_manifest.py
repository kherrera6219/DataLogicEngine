"""Canonical provider/model contract shared by backend, UI, tests, and docs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(__file__).resolve().parents[2] / "config" / "provider_manifest.v1.json"
EXPECTED_SCHEMA_VERSION = "provider-manifest.v1"


@dataclass(frozen=True, slots=True)
class ProviderModel:
    id: str
    label: str
    minimum_output_tokens: int


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    id: str
    label: str
    aliases: tuple[str, ...]
    default_model: str
    models: tuple[ProviderModel, ...]
    api_key_environment: tuple[str, ...]
    base_url_environment: str | None
    request_api: str
    native_streaming: bool
    buffered_output: bool
    pricing_status: str
    pricing_reason: str

    @property
    def model_ids(self) -> tuple[str, ...]:
        return tuple(model.id for model in self.models)


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Provider manifest field {field!r} must be non-empty")
    return text


def _load_manifest() -> tuple[dict[str, Any], tuple[ProviderDefinition, ...]]:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if raw.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("Unsupported provider manifest schema version")

    providers: list[ProviderDefinition] = []
    claimed_names: set[str] = set()
    for entry in raw.get("providers") or []:
        provider_id = _required_text(entry.get("id"), "providers[].id").lower()
        aliases = tuple(
            _required_text(alias, f"providers[{provider_id}].aliases[]").lower()
            for alias in entry.get("aliases") or []
        )
        names = {provider_id, *aliases}
        if names & claimed_names:
            raise ValueError(f"Duplicate provider id or alias: {sorted(names & claimed_names)}")
        claimed_names.update(names)

        models = tuple(
            ProviderModel(
                id=_required_text(model.get("id"), f"providers[{provider_id}].models[].id"),
                label=_required_text(model.get("label"), f"providers[{provider_id}].models[].label"),
                minimum_output_tokens=max(1, int(model.get("minimum_output_tokens") or 1)),
            )
            for model in entry.get("models") or []
        )
        default_model = _required_text(
            entry.get("default_model"), f"providers[{provider_id}].default_model"
        )
        if default_model not in {model.id for model in models}:
            raise ValueError(f"Default model {default_model!r} is not declared for {provider_id}")

        capabilities = entry.get("capabilities") or {}
        pricing = entry.get("pricing") or {}
        providers.append(
            ProviderDefinition(
                id=provider_id,
                label=_required_text(entry.get("label"), f"providers[{provider_id}].label"),
                aliases=aliases,
                default_model=default_model,
                models=models,
                api_key_environment=tuple(
                    _required_text(name, f"providers[{provider_id}].api_key_environment[]")
                    for name in entry.get("api_key_environment") or []
                ),
                base_url_environment=(
                    str(entry["base_url_environment"]).strip()
                    if entry.get("base_url_environment")
                    else None
                ),
                request_api=_required_text(
                    entry.get("request_api"), f"providers[{provider_id}].request_api"
                ),
                native_streaming=bool(capabilities.get("native_streaming")),
                buffered_output=bool(capabilities.get("buffered_output")),
                pricing_status=_required_text(
                    pricing.get("status"), f"providers[{provider_id}].pricing.status"
                ),
                pricing_reason=_required_text(
                    pricing.get("reason"), f"providers[{provider_id}].pricing.reason"
                ),
            )
        )

    if not providers:
        raise ValueError("Provider manifest must declare at least one provider")
    return raw, tuple(providers)


RAW_PROVIDER_MANIFEST, PROVIDERS = _load_manifest()
PROVIDERS_BY_ID = {provider.id: provider for provider in PROVIDERS}
PROVIDER_ALIASES = {
    name: provider.id
    for provider in PROVIDERS
    for name in (provider.id, *provider.aliases)
}
SUPPORTED_PROVIDER_TYPES = frozenset(PROVIDERS_BY_ID)
DEFAULT_MODEL_BY_PROVIDER = {
    provider.id: provider.default_model for provider in PROVIDERS
}


def normalize_provider_type(provider_type: str | None) -> str:
    """Return the canonical supported provider id or fail closed."""
    normalized = str(provider_type or "").strip().lower()
    canonical = PROVIDER_ALIASES.get(normalized)
    if canonical is None:
        raise ValueError(f"Unsupported provider: {normalized or '<missing>'}")
    return canonical


def provider_definition(provider_type: str | None) -> ProviderDefinition:
    return PROVIDERS_BY_ID[normalize_provider_type(provider_type)]


def default_model_for_provider(provider_type: str | None) -> str:
    return provider_definition(provider_type).default_model


def validate_provider_model(provider_type: str | None, model: str | None) -> str:
    provider = provider_definition(provider_type)
    selected = str(model or provider.default_model).strip()
    if selected not in provider.model_ids:
        raise ValueError(f"Unsupported model {selected!r} for provider {provider.id}")
    return selected
