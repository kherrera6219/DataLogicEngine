from pathlib import Path

import yaml

from backend.knowledge_algorithms.production_catalog import (
    KAClassification,
    load_production_catalog,
    validate_production_catalog,
)


def _registry_ids() -> set[str]:
    path = Path("backend/knowledge_algorithms/ka_registry.yaml")
    return set((yaml.safe_load(path.read_text(encoding="utf-8")) or {})["ka_registry"])


def test_every_registered_ka_has_valid_production_classification():
    catalog = load_production_catalog()
    registry_ids = _registry_ids()

    assert len(registry_ids) == 125
    assert set(catalog) == registry_ids
    assert validate_production_catalog(catalog) == []
    assert {entry.classification for entry in catalog.values()} <= set(KAClassification)


def test_experimental_and_placeholder_algorithms_are_disabled_by_default():
    catalog = load_production_catalog()

    assert catalog["KA-032"].classification is KAClassification.EXPERIMENTAL_METHOD
    assert catalog["KA-032"].production_enabled is False
    assert catalog["KA-033"].classification is KAClassification.PLACEHOLDER_NOT_PRODUCTION_ENABLED
    assert catalog["KA-033"].production_enabled is False
    assert catalog["KA-001"].production_enabled is True
    assert catalog["KA-113"].production_enabled is True
