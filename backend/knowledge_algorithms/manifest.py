"""Validated loader and identity resolver for the canonical KA manifest."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

MANIFEST_PATH = Path(__file__).with_name("ka_manifest.v1.generated.json")


def normalize_ka_id(value: str) -> str:
    clean = str(value).strip()
    if ":" in clean:
        scope, source_id = clean.split(":", 1)
        return f"{scope.lower()}:{normalize_ka_id(source_id)}"
    upper = clean.upper()
    if upper == "KA-MASTER":
        return "KA-Master"
    layer_match = re.fullmatch(r"(L(?:9|10)-KA-)(\d+)", upper)
    if layer_match:
        return f"{layer_match.group(1)}{int(layer_match.group(2)):03d}"
    numeric_match = re.fullmatch(r"(?:KA-)?(\d+)", upper)
    if numeric_match:
        number = int(numeric_match.group(1))
        width = 3 if number < 1000 else 4
        return f"KA-{number:0{width}d}"
    return clean


class KAEntrypoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter: str
    module: str
    callable: str
    class_name: str | None = None


class KAImplementation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    source: str | None = None
    entrypoint: KAEntrypoint | None = None


class KAContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    status: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    layers: list[str] = Field(default_factory=list)
    personas: list[str] = Field(default_factory=list)
    subsystems: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    risk_classes: list[str] = Field(default_factory=list)
    effect_class: str
    reads_memory: bool = False
    writes_memory: bool = False
    produces_artifacts: bool = False
    audit_events: bool = True
    limitations: str
    guarantee: str
    performance_budget_ms: int = Field(gt=0)


class KAAdmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    production_enabled: bool
    classification: str
    deterministic: bool | None = None
    direct_execution: str


class KADefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str
    name: str
    purpose: str | None = None
    version: str
    identity_class: str
    aliases: dict[str, list[str]]
    implementation: KAImplementation
    contract: KAContract
    admission: KAAdmission
    migration_notes: str


class KAManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    manifest_version: str
    status: str
    authority: dict[str, Any]
    capability_count: int = Field(gt=0)
    alias_index: dict[str, str]
    entries: dict[str, KADefinition]

    @model_validator(mode="after")
    def validate_authority(self) -> KAManifest:
        if self.capability_count != len(self.entries):
            raise ValueError("capability_count does not match entries")
        normalized_names: dict[str, str] = {}
        normalized_purposes: dict[str, str] = {}
        contract_signatures: dict[
            tuple[str, tuple[str, ...], tuple[str, ...]], str
        ] = {}
        declared_aliases: dict[str, str] = {}
        for key, definition in self.entries.items():
            if key != definition.canonical_id:
                raise ValueError(f"manifest key/id mismatch for {key}")
            name_key = _semantic_key(definition.name)
            prior_name = normalized_names.setdefault(name_key, key)
            if prior_name != key:
                raise ValueError(
                    f"duplicate canonical name for {prior_name} and {key}"
                )
            if definition.purpose:
                purpose_key = _semantic_key(definition.purpose)
                prior_purpose = normalized_purposes.setdefault(purpose_key, key)
                if prior_purpose != key:
                    raise ValueError(
                        f"duplicate canonical purpose for {prior_purpose} and {key}"
                    )
            signature = (
                _semantic_key(definition.purpose or ""),
                tuple(_semantic_key(value) for value in definition.contract.inputs),
                tuple(_semantic_key(value) for value in definition.contract.outputs),
            )
            if any(signature):
                prior_contract = contract_signatures.setdefault(signature, key)
                if prior_contract != key:
                    raise ValueError(
                        f"duplicate canonical contract for {prior_contract} and {key}"
                    )
            if bool(definition.implementation.source) != bool(
                definition.implementation.entrypoint
            ):
                raise ValueError(f"{key}: implementation source/entrypoint mismatch")
            for dependency in definition.contract.dependencies:
                if dependency not in self.entries:
                    raise ValueError(f"{key}: unknown dependency {dependency}")
            if definition.aliases.get("unscoped"):
                raise ValueError(f"{key}: unscoped compatibility aliases are forbidden")
            for alias in definition.aliases.get("scoped", []):
                prior_alias = declared_aliases.setdefault(alias, key)
                if prior_alias != key:
                    raise ValueError(
                        f"{alias}: alias declared for both {prior_alias} and {key}"
                    )
        for alias, canonical_id in self.alias_index.items():
            if canonical_id not in self.entries:
                raise ValueError(f"{alias}: alias target does not exist")
            if alias in self.entries:
                raise ValueError(f"{alias}: alias collides with canonical ID")
        if declared_aliases != self.alias_index:
            raise ValueError("entry aliases do not match the manifest alias index")
        return self

    def resolve_id(self, value: str, *, allow_scoped_alias: bool = False) -> str:
        normalized = normalize_ka_id(value)
        if normalized in self.entries:
            return normalized
        if allow_scoped_alias and normalized in self.alias_index:
            return self.alias_index[normalized]
        raise KeyError(value)

    def get(
        self, value: str, *, allow_scoped_alias: bool = False
    ) -> KADefinition:
        return self.entries[
            self.resolve_id(value, allow_scoped_alias=allow_scoped_alias)
        ]


def _semantic_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


@lru_cache(maxsize=4)
def load_manifest(path: str | Path = MANIFEST_PATH) -> KAManifest:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return KAManifest.model_validate(payload)
