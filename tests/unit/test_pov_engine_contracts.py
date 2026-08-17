"""Deterministic contracts for POV expansion and persona construction."""

from unittest.mock import patch

import pytest

from core.simulation.pov_engine import POVEngine


def make_engine(**config):
    return POVEngine(
        {
            "confidence_threshold": config.pop("confidence_threshold", 0.0),
            "max_recursive_passes": config.pop("max_recursive_passes", 2),
            **config,
        }
    )


def rich_context():
    return {
        "simulation_id": "simulation",
        "query": (
            "technology software healthcare finance government education manufacturing energy "
            "transportation telecom GDPR HIPAA ISO 27001 NIST 800-53 PCI DSS CMMC"
        ),
        "initial_data": [
            {"node_id": "one", "pl_level": "PL10", "sectors": ["Sector6"]},
            {
                "node_id": "two",
                "axis_mappings": {"axis_1_pillar": "PL11", "axis_2_sector": "Sector2"},
            },
        ],
    }


def test_process_and_expansion_full_layer_contract_is_deterministic():
    engine = make_engine(enabled_axes=[1, 2, 3, 8, 9, 10, 11, 12, 13])
    with patch("core.simulation.pov_engine.random.random", return_value=0.5), patch(
        "core.simulation.pov_engine.random.choice", side_effect=lambda values: list(values)[0]
    ):
        result = engine.process({"query_text": rich_context()["query"], **rich_context()})
    assert len(result["expanded_data"]) == 5
    assert len(result["simulated_personas"]) == 4
    assert result["temporal_spatial"]["spatial"]["primary_location"] == "United States"
    assert result["entangled_viewpoints"]["entangled"]
    assert result["pov_stats"]["passes"] == 1
    assert result["pov_stats"]["axis_coverage"]["axis_3"] == 0.9
    stats = engine.get_stats()
    assert stats["simulation_id"] == "simulation"
    assert stats["context_size"] > 0
    assert sum(axis["enabled"] for axis in engine.ukg_axes.values()) == 9


def test_recursive_expansion_disabled_personas_temporal_and_empty_query_paths():
    recursive = make_engine(confidence_threshold=1.0, max_recursive_passes=2)
    result = recursive.expand_context("q", {"initial_data": []})
    assert result["pov_stats"]["passes"] == 2
    assert result["pov_stats"]["recursion_depth"] == 1

    minimal = make_engine(enable_persona_layer=False, enable_temporal_mapping=False)
    result = minimal.process({})
    assert "simulated_personas" not in result
    assert "temporal_spatial" not in result
    assert not result["entangled_viewpoints"]["entangled"]


def test_extractors_defaults_duplicates_keywords_and_framework_mentions():
    engine = make_engine()
    assert engine._extract_pl_levels(None) == []
    assert engine._extract_sectors(None) == []
    assert engine._extract_regulatory_mentions(None) == []
    assert engine._extract_compliance_frameworks(None) == []
    context = rich_context()
    pls = engine._extract_pl_levels(context)
    sectors = engine._extract_sectors(context)
    assert "PL10" in pls and "PL11" in pls
    assert len(pls) == len(set(pls))
    assert "Sector1" in sectors and "Sector2" in sectors and "Sector6" in sectors
    assert len(sectors) == len(set(sectors))
    regulatory = engine._extract_regulatory_mentions(context)
    compliance = engine._extract_compliance_frameworks(context)
    assert "GDPR" in regulatory and "HIPAA" in regulatory
    assert "ISO 27001" in compliance and "NIST 800-53" in compliance

    default_expansion = engine._expand_data_via_honeycomb({"initial_data": []})
    assert len(default_expansion) == 3
    assert {node["axis_mappings"]["axis_1_pillar"] for node in default_expansion}


@pytest.mark.parametrize(
    ("persona_type", "pl_levels", "sectors"),
    [
        ("knowledge", ["PL10"], ["Sector6"]),
        ("knowledge", ["PL01"], []),
        ("knowledge", ["PL02"], []),
        ("sector", [], ["Sector1"]),
        ("sector", [], ["Sector2"]),
        ("sector", [], ["Sector6"]),
        ("regulatory", [], ["Sector1"]),
        ("regulatory", [], ["Sector2"]),
        ("compliance", [], ["Sector1"]),
        ("compliance", [], ["Sector2"]),
        ("compliance", [], ["Sector6"]),
        ("custom", [], []),
    ],
)
def test_all_persona_component_types(persona_type, pl_levels, sectors):
    engine = make_engine()
    components = [
        "job_role",
        "education",
        "certifications",
        "skills",
        "training",
        "career_path",
        "related_jobs",
    ]
    generated = [
        engine._generate_component(component, persona_type, pl_levels, sectors)
        for component in components
    ]
    assert all(item["type"] in components for item in generated)
    assert all(0.7 <= item["relevance"] <= 0.9 for item in generated)


def test_expertise_mapping_perspective_variants_and_persona_simulation():
    engine = make_engine()
    assert engine._map_expertise_areas(None, None)["knowledge"]
    expertise = engine._map_expertise_areas(
        ["PL01", "PL02", "PL06", "PL11", "PL15", "PL16"],
        ["Sector1", "Sector2", "Sector3", "Sector8"],
    )
    assert "mathematical_modeling" in expertise["knowledge"]
    assert "legislative_frameworks" in expertise["regulatory"]
    assert "industry_standards" in expertise["compliance"]
    for persona_type in ("knowledge", "sector", "regulatory", "compliance", "custom"):
        perspective = engine._generate_perspective(rich_context(), persona_type, expertise)
        assert len(perspective["key_points"]) == 3
        assert len(perspective["evidence"]) == 2
    assert engine._generate_perspective({"query": "q"}, "custom")["confidence"] == 0.75
    personas = engine._simulate_personas(rich_context())
    assert [persona["axis"] for persona in personas] == [8, 9, 10, 11]
    assert engine.personas_generated == 4


def test_entanglement_belief_relationships_and_confidence_inputs():
    engine = make_engine()
    assert engine._entangle_viewpoints(None) == {}
    empty = engine._entangle_viewpoints({})
    assert not empty["entangled"]
    assert engine._generate_belief_matrix(None) == {}

    personas = engine._simulate_personas(rich_context())
    matrix = engine._generate_belief_matrix(personas)
    assert set(matrix) == {persona["persona_id"] for persona in personas}
    assert all(0.5 <= value <= 1.0 for value in matrix.values())
    assert engine._apply_cross_persona_relationships([personas[0]], matrix) is None
    entangled = engine._entangle_viewpoints({"simulated_personas": personas})
    assert entangled["source_count"] == 4
    assert entangled["points"]

    confidence = engine._calculate_confidence(
        {
            "personas": personas,
            "belief_matrix": matrix,
            "expanded_data": [{}, {}, {}],
            "temporal_mapping": {"temporal_coverage": 0.9},
        }
    )
    assert confidence > 0.8
    assert engine._calculate_confidence({}) == 0.0
    assert engine._calculate_confidence({"expanded_data": [{}]}) == 0.66
    assert engine._calculate_axis_coverage({})["axis_13"] == 0.7
