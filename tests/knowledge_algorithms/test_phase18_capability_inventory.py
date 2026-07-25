from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_ka_capability_inventory.py"


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location(
        "build_ka_capability_inventory", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


INVENTORY_MODULE = _load_inventory_module()


def test_phase18_inventory_classifies_every_known_definition_without_loss():
    inventory, crosswalk = INVENTORY_MODULE.build_inventory()

    assert inventory["summary"]["live_registry_entries"] == 125
    assert inventory["summary"]["unregistered_layer9_implementations"] == 7
    assert inventory["summary"]["original_design_rows"] == 114
    assert inventory["summary"]["core_metadata_rows"] == 277
    assert inventory["summary"]["sdk_registry_rows"] == 114
    assert inventory["summary"]["unclassified_source_definitions"] == 0
    assert (
        inventory["summary"]["implementation_surfaces"]
        == crosswalk["summary"]["existing_implementation_proposals"]
    )
    assert inventory["summary"]["unclassified_implementation_surfaces"] == 0
    assert inventory["summary"]["unclassified_integration_surfaces"] == 0
    assert crosswalk["summary"]["canonical_capability_proposals"] == 213
    assert crosswalk["summary"]["existing_implementation_proposals"] >= 132
    assert crosswalk["summary"]["implementation_required_proposals"] <= 81
    assert (
        crosswalk["summary"]["existing_implementation_proposals"]
        + crosswalk["summary"]["implementation_required_proposals"]
        == 213
    )
    assert crosswalk["summary"]["semantic_duplicate_aliases"] == 1
    assert crosswalk["summary"]["reviewed_distinct_candidate_pairs"] == 11
    assert crosswalk["summary"]["unresolved_semantic_duplicate_candidates"] == 0
    assert crosswalk["summary"]["exact_canonical_name_collisions"] == 0
    assert crosswalk["summary"]["exact_canonical_purpose_collisions"] == 0
    assert crosswalk["summary"]["exact_canonical_contract_collisions"] == 0


def test_phase18_crosswalk_preserves_current_and_restored_colliding_semantics():
    _inventory, crosswalk = INVENTORY_MODULE.build_inventory()
    rows = {row["canonical_id"]: row for row in crosswalk["canonical_capabilities"]}

    assert rows["KA-036"]["name"] == "Complexity Estimator"
    assert rows["KA-036"]["implementation"]
    assert rows["KA-1036"]["name"] == "Pareto Optimization Engine"
    assert rows["KA-1036"]["implementation"].endswith(
        "ka_1036_pareto_optimization_engine.py"
    )
    assert "design-v1:KA-036" in rows["KA-1036"]["scoped_aliases"]
    assert rows["KA-117"]["name"] == "Knowledge Integrity Validator"
    assert "design-v1:KA-050" in rows["KA-117"]["scoped_aliases"]
    assert rows["KA-113"]["name"] == "Complexity Router"
    assert "design-v1:KA-113" not in rows["KA-113"]["scoped_aliases"]
    original_113 = [
        row
        for row in rows["KA-113"]["source_records"]
        if row["source_id"] == "KA-113"
        and row["source"].endswith("data/registries/ka_registry.yaml")
    ]
    assert len(original_113) == 1
    assert original_113[0]["rationale"] == "reviewed semantic-equivalence alias"


def test_phase18_crosswalk_classifies_generic_scaffolds_as_history():
    inventory, crosswalk = INVENTORY_MODULE.build_inventory()

    generic = [
        row
        for row in inventory["source_definitions"]
        if row["disposition"] == "generated_generic_scaffold"
    ]
    canonical_ids = {row["canonical_id"] for row in crosswalk["canonical_capabilities"]}

    assert len(generic) == 64
    assert all(row["canonical_id"] is None for row in generic)
    assert "KA-214" not in canonical_ids
    assert "KA-277" not in canonical_ids


def test_phase18_crosswalk_collapses_true_duplicates_and_reviews_similar_kas():
    _inventory, crosswalk = INVENTORY_MODULE.build_inventory()
    rows = {row["canonical_id"]: row for row in crosswalk["canonical_capabilities"]}

    assert "KA-133" not in rows
    assert "generated-v1:KA-133" in rows["KA-1101"]["scoped_aliases"]
    assert rows["L10-KA-006"]["name"] == "Layer-10 Belief-Decay Trust Gate"
    assert crosswalk["duplicate_review"]["unresolved_candidates"] == []
    assert all(
        row["disposition"] == "reviewed_materially_distinct"
        for row in crosswalk["duplicate_review"]["reviewed_candidate_pairs"]
    )


def test_phase18_generated_inventory_is_current(tmp_path):
    expected = INVENTORY_MODULE.output_payloads(tmp_path)

    assert {path.name for path in expected} == {
        "ka-capability-crosswalk.csv",
        "ka-capability-crosswalk.json",
        "ka-capability-inventory.json",
        "ka-capability-inventory-summary.md",
    }
    parsed = json.loads(expected[tmp_path / "ka-capability-crosswalk.json"])
    assert parsed["status"] == "approved_cp18_a_authority"
    assert parsed["summary"]["unclassified_source_definitions"] == 0
