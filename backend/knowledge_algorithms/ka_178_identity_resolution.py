"""KA-178: deterministic exact-identifier identity resolution."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class IdentityIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier_type: Literal["email", "employee_id", "external_id", "username"]
    value: str = Field(min_length=1, max_length=500)
    verified: bool


class IdentityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(min_length=1, max_length=200)
    identifiers: list[IdentityIdentifier] = Field(min_length=1, max_length=100)


class KA178Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "records": [
                        {
                            "record_id": "r1",
                            "identifiers": [
                                {
                                    "identifier_type": "email",
                                    "value": "Owner@Example.com",
                                    "verified": True,
                                }
                            ],
                        },
                        {
                            "record_id": "r2",
                            "identifiers": [
                                {
                                    "identifier_type": "email",
                                    "value": "owner@example.com",
                                    "verified": True,
                                }
                            ],
                        },
                    ]
                }
            ]
        },
    )

    records: list[IdentityRecord] = Field(min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA178Input:
        identifiers = [item.record_id for item in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("record IDs must be unique")
        return self


class KA178IdentityResolution(KnowledgeAlgorithm):
    """Merge records only through shared verified exact identifiers."""

    input_schema = KA178Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-178"

    @staticmethod
    def _normalized(identifier: IdentityIdentifier) -> str:
        value = re.sub(r"\s+", "", identifier.value)
        if identifier.identifier_type in {"email", "username"}:
            value = value.casefold()
        return f"{identifier.identifier_type}:{value}"

    def _run_logic(self, input_data: KA178Input) -> dict[str, Any]:
        parents = {item.record_id: item.record_id for item in input_data.records}

        def find(value: str) -> str:
            while parents[value] != value:
                parents[value] = parents[parents[value]]
                value = parents[value]
            return value

        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parents[max(left_root, right_root)] = min(left_root, right_root)

        owners: dict[str, str] = {}
        for record in sorted(input_data.records, key=lambda row: row.record_id):
            for identifier in record.identifiers:
                if not identifier.verified:
                    continue
                key = self._normalized(identifier)
                if key in owners:
                    union(record.record_id, owners[key])
                else:
                    owners[key] = record.record_id
        clusters: dict[str, list[str]] = defaultdict(list)
        for record_id in sorted(parents):
            clusters[find(record_id)].append(record_id)
        return {
            "success": True,
            "status": "identities_resolved",
            "clusters": [
                {
                    "canonical_record_id": min(record_ids),
                    "record_ids": sorted(record_ids),
                    "match_basis": "shared_verified_exact_identifier",
                }
                for record_ids in sorted(clusters.values())
            ],
            "records_merged": 0,
            "deterministic": True,
            "limitations": (
                "Only shared verified exact identifiers create links; fuzzy names "
                "and unverified identifiers never cause an automatic merge."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA178IdentityResolution(context).run(context)
