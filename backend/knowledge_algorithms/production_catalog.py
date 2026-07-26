"""Production classification and governance for all registered KAs."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

import yaml


class KAClassification(StrEnum):
    PRODUCTION_VALIDATOR = "production_validator"
    DETERMINISTIC_HEURISTIC = "deterministic_heuristic"
    EXPERIMENTAL_METHOD = "experimental_method"
    PRESENTATION_TEMPLATE_HELPER = "presentation_template_helper"
    PLACEHOLDER_NOT_PRODUCTION_ENABLED = "placeholder_not_production_enabled"


@dataclass(frozen=True, slots=True)
class KAProductionEntry:
    ka_id: str
    implementation: str
    classification: KAClassification
    production_enabled: bool
    deterministic: bool
    guarantee: str
    version: str = "ka-catalog.v1"
    limitations: str = ""
    input_contract: str = "versioned Pydantic or documented dictionary input"
    evidence_requirement: str = (
        "category-specific observed inputs; no inferred factual proof"
    )
    test_reference: str = "tests/knowledge_algorithms/test_production_invariants.py"
    performance_budget_ms: int = 1000
    documentation_reference: str = "docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["classification"] = self.classification.value
        return payload


_PRODUCTION_VALIDATORS = {
    "KA-004",
    "KA-009",
    "KA-024",
    "KA-061",
    "KA-074",
    "KA-117",
    "L9-KA-001",
    "L9-KA-003",
    "L9-KA-005",
    "L9-KA-007",
    "L10-KA-003",
    "L10-KA-005",
    "L10-KA-006",
    "L10-KA-007",
}
_PRODUCTION_HEURISTICS = {
    "KA-001",
    "KA-003",
    "KA-005",
    "KA-011",
    "KA-012",
    "KA-013",
    "KA-025",
    "KA-030",
    "KA-113",
    "L9-KA-002",
    "L9-KA-004",
    "L9-KA-006",
    "L10-KA-001",
    "L10-KA-002",
    "L10-KA-004",
}
_EXPERIMENTAL = {
    "KA-002",
    "KA-006",
    "KA-007",
    "KA-008",
    "KA-020",
    "KA-021",
    "KA-028",
    "KA-029",
    "KA-032",
    "KA-034",
    "KA-035",
    "KA-038",
    "KA-040",
    "KA-041",
    "KA-042",
    "KA-043",
    "KA-051",
    "KA-054",
    "KA-055",
    "KA-057",
    "KA-058",
    "KA-059",
    "KA-063",
    "KA-066",
    "KA-067",
    "KA-068",
    "KA-069",
    "KA-070",
    "KA-081",
    "KA-082",
    "KA-083",
    "KA-085",
    "KA-086",
    "KA-088",
    "KA-089",
    "KA-090",
    "KA-100",
    "KA-Master",
}
_PRESENTATION_HELPERS = {
    "KA-056",
    "KA-091",
    "KA-092",
    "KA-093",
    "KA-094",
    "KA-095",
}
_PLACEHOLDERS = {"KA-033"}


def load_production_catalog(
    registry_path: str | Path | None = None,
) -> dict[str, KAProductionEntry]:
    path = (
        Path(registry_path)
        if registry_path
        else Path(__file__).with_name("ka_registry.yaml")
    )
    registry = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(
        "ka_registry", {}
    )
    return {
        str(ka_id): _entry(str(ka_id), str(implementation))
        for ka_id, implementation in registry.items()
    }


def validate_production_catalog(
    catalog: Mapping[str, KAProductionEntry] | None = None,
    *,
    check_references: bool | None = None,
) -> list[str]:
    rows = dict(catalog or load_production_catalog())
    root = Path(__file__).resolve().parents[2]
    if check_references is None:
        check_references = not bool(getattr(sys, "frozen", False))
    errors: list[str] = []
    for ka_id, entry in rows.items():
        if ka_id != entry.ka_id:
            errors.append(f"{ka_id}: catalog key/id mismatch")
        module_path = entry.implementation.rsplit(".", 1)[0]
        source = root / Path(*module_path.split(".")).with_suffix(".py")
        if check_references and not source.exists():
            errors.append(f"{ka_id}: implementation missing: {source}")
        if entry.production_enabled and entry.classification not in {
            KAClassification.PRODUCTION_VALIDATOR,
            KAClassification.DETERMINISTIC_HEURISTIC,
        }:
            errors.append(f"{ka_id}: non-production category enabled")
        if entry.production_enabled and not entry.deterministic:
            errors.append(f"{ka_id}: production-enabled algorithm is not deterministic")
        if (
            entry.classification
            in {
                KAClassification.EXPERIMENTAL_METHOD,
                KAClassification.PLACEHOLDER_NOT_PRODUCTION_ENABLED,
            }
            and entry.production_enabled
        ):
            errors.append(f"{ka_id}: experimental/placeholder enabled by default")
        required_metadata = (
            entry.guarantee,
            entry.limitations,
            entry.input_contract,
            entry.evidence_requirement,
            entry.test_reference,
            entry.documentation_reference,
        )
        if not all(required_metadata) or entry.performance_budget_ms <= 0:
            errors.append(f"{ka_id}: category contract metadata incomplete")
        if check_references and not (root / entry.test_reference).exists():
            errors.append(f"{ka_id}: production test reference missing")
        if check_references and not (root / entry.documentation_reference).exists():
            errors.append(f"{ka_id}: documentation reference missing")
    return errors


def _entry(ka_id: str, implementation: str) -> KAProductionEntry:
    if ka_id in _PLACEHOLDERS:
        classification = KAClassification.PLACEHOLDER_NOT_PRODUCTION_ENABLED
    elif ka_id in _PRESENTATION_HELPERS:
        classification = KAClassification.PRESENTATION_TEMPLATE_HELPER
    elif ka_id in _EXPERIMENTAL:
        classification = KAClassification.EXPERIMENTAL_METHOD
    elif ka_id in _PRODUCTION_VALIDATORS:
        classification = KAClassification.PRODUCTION_VALIDATOR
    else:
        classification = KAClassification.DETERMINISTIC_HEURISTIC

    production_enabled = ka_id in (_PRODUCTION_VALIDATORS | _PRODUCTION_HEURISTICS)
    deterministic = ka_id not in {"KA-008", "KA-028"}
    guarantees = {
        KAClassification.PRODUCTION_VALIDATOR: (
            "Validates only its documented input contract and fails closed when required evidence is absent."
        ),
        KAClassification.DETERMINISTIC_HEURISTIC: (
            "Produces a repeatable heuristic result for identical versioned inputs; it is not independent factual proof."
        ),
        KAClassification.EXPERIMENTAL_METHOD: (
            "Provides research or exploratory output only and is excluded from production answer validation."
        ),
        KAClassification.PRESENTATION_TEMPLATE_HELPER: (
            "Formats or presents supplied data and never establishes evidence, correctness, or compliance."
        ),
        KAClassification.PLACEHOLDER_NOT_PRODUCTION_ENABLED: (
            "Provides no production behavior or assurance and is disabled."
        ),
    }
    limitations = {
        KAClassification.PRODUCTION_VALIDATOR: (
            "Guarantee is limited to deterministic contract checks and versioned semantic fixtures."
        ),
        KAClassification.DETERMINISTIC_HEURISTIC: (
            "Named scores and classifications are heuristics, not calibrated probabilities."
        ),
        KAClassification.EXPERIMENTAL_METHOD: (
            "Requires explicit owner opt-in, recorded parameters/seed when stochastic, and cannot appear as a production validator."
        ),
        KAClassification.PRESENTATION_TEMPLATE_HELPER: (
            "Output quality depends entirely on supplied content and must be labeled as presentation."
        ),
        KAClassification.PLACEHOLDER_NOT_PRODUCTION_ENABLED: (
            "Execution is rejected in production workflows."
        ),
    }
    return KAProductionEntry(
        ka_id=ka_id,
        implementation=implementation,
        classification=classification,
        production_enabled=production_enabled,
        deterministic=deterministic,
        guarantee=guarantees[classification],
        limitations=limitations[classification],
    )
