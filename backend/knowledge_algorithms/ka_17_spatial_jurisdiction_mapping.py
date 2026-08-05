"""KA-017: supplied jurisdiction-context matching."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class JurisdictionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jurisdiction_id: str = Field(min_length=1, max_length=100)
    location_aliases: list[str] = Field(min_length=1, max_length=100)
    entity_scopes: list[str] = Field(default_factory=list, max_length=100)
    regulation_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA017Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str = Field(min_length=1, max_length=500)
    entity_scope: str = Field(min_length=1, max_length=500)
    candidates: list[JurisdictionCandidate] = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA017Input:
        ids = [item.jurisdiction_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("jurisdiction candidate IDs must be unique")
        return self


class KA017SpatialMapping(KnowledgeAlgorithm):
    """Match declared jurisdiction candidates without inventing legal applicability."""

    input_schema = KA017Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-017"

    def _run_logic(self, input_data: KA017Input) -> dict[str, Any]:
        location = input_data.location.strip().casefold()
        scope = input_data.entity_scope.strip().casefold()
        matches = []
        for candidate in input_data.candidates:
            aliases = {value.strip().casefold() for value in candidate.location_aliases}
            scopes = {value.strip().casefold() for value in candidate.entity_scopes}
            location_match = location in aliases
            scope_match = not scopes or scope in scopes
            if location_match and scope_match:
                matches.append(
                    {
                        "jurisdiction_id": candidate.jurisdiction_id,
                        "regulation_refs": sorted(set(candidate.regulation_refs)),
                        "match_basis": [
                            "declared_location_alias",
                            *(["declared_entity_scope"] if scopes else []),
                        ],
                    }
                )
        matches.sort(key=lambda item: item["jurisdiction_id"])
        return {
            "success": True,
            "status": "jurisdiction_context_matched"
            if matches
            else "no_declared_match",
            "matches": matches,
            "resolved_jurisdiction": (
                matches[0]["jurisdiction_id"] if len(matches) == 1 else None
            ),
            "legal_applicability_established": False,
            "external_lookup_performed": False,
            "deterministic": True,
            "limitations": (
                "Matches only caller-supplied aliases, scopes, and regulation "
                "references; legal applicability requires authoritative review."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA017SpatialMapping(context).run(context)
