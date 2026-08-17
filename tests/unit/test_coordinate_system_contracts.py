"""Behavioral contracts for the 17-axis coordinate value objects and traversal facade."""

import pytest

from core.coordinate_system import (
    AxisCoordinate,
    CoordinateParser,
    CoordinateResolver,
    CrosswalkTraversal,
    UnifiedCoordinate,
    create_coordinate_system,
)


def test_axis_coordinate_hierarchy_serialization_and_relationships():
    parent = AxisCoordinate(1, "32.2", meta_tag="FAR", description="parent")
    child = AxisCoordinate(1, "32.2.7")
    assert child.depth == 3
    assert child.parent_coordinate == "32.2"
    assert child.is_descendant_of(parent)
    assert not parent.is_descendant_of(child)
    assert not child.is_descendant_of(AxisCoordinate(2, "32"))
    assert str(parent) == "FAR.32.2"
    assert str(child) == "1.32.2.7"
    assert parent.to_dict()["description"] == "parent"
    assert AxisCoordinate(1, "word").levels == []
    assert AxisCoordinate(1, "1").parent_coordinate is None


def test_unified_coordinate_round_trip_matching_and_validation():
    coordinate = UnifiedCoordinate()
    coordinate.set_axis(1, "32.2", "FAR", "pillar")
    coordinate.set_axis(2, "54.7")
    coordinate.set_axis(3, None)
    coordinate.set_axis(4, "letters")
    assert coordinate.get_dimension_count() == 4
    assert coordinate.get_axis(1).meta_tag == "FAR"
    assert coordinate.to_tuple()[1] == "54.7"
    assert "FAR.32.2" in coordinate.to_coordinate_string()
    assert "A2:54.7" in coordinate.to_short_string()
    payload = coordinate.to_dict()
    restored = UnifiedCoordinate.from_dict(payload)
    assert restored.matches_partial(UnifiedCoordinate.from_dict({"coordinates": [payload["coordinates"][0]]}))
    mismatch = UnifiedCoordinate()
    mismatch.set_axis(2, "99")
    assert not coordinate.matches_partial(mismatch)
    absent = UnifiedCoordinate()
    absent.set_axis(17, "2")
    assert not coordinate.matches_partial(absent)
    with pytest.raises(ValueError):
        coordinate.set_axis(0, "1")
    with pytest.raises(ValueError):
        coordinate.set_axis("1", "1")

    full = UnifiedCoordinate()
    for axis in range(1, 18):
        full.set_axis(axis, "1")
    assert full.is_fully_specified()


def test_parser_accepts_meta_axis_colon_pipe_and_partial_errors():
    assert CoordinateParser.parse_axis_coordinate("FAR.1.2").axis_number == 1
    assert CoordinateParser.parse_axis_coordinate("2.54.7").value == "54.7"
    assert CoordinateParser.parse_axis_coordinate("2.54", 2).value == "54"
    with pytest.raises(ValueError):
        CoordinateParser.parse_axis_coordinate("unknown")
    assert CoordinateParser.parse_full_coordinate("").get_dimension_count() == 0
    assert CoordinateParser.parse_full_coordinate("FAR.1.2 | NAICS.54 | bad").get_dimension_count() == 2
    colon = CoordinateParser.parse_full_coordinate("1.2:2.54:*:4.3")
    assert colon.get_dimension_count() == 3
    assert CoordinateParser.parse_full_coordinate("1.32").get_axis(1).value == "32"
    long_value = ":".join("1" for _ in range(19))
    assert CoordinateParser.parse_full_coordinate(long_value).get_dimension_count() == 17


def test_resolver_covers_all_axis_context_types_and_risk_bands():
    resolver = CoordinateResolver()
    coordinate = UnifiedCoordinate()
    values = {
        1: "32.2",
        2: "54.7.1.2",
        3: "1",
        4: "2",
        5: "3",
        6: "1",
        7: "2",
        8: "1.2",
        9: "2.3",
        10: "3.4",
        11: "4.5",
        12: "1.2.3",
        13: "2026.8.1",
        14: "4.2.1",
        15: "85.2",
        16: "3.2",
        17: "5",
    }
    for axis, value in values.items():
        coordinate.set_axis(axis, value)
    resolved = resolver.resolve_full_coordinate(coordinate)
    assert len(resolved["axes"]) == 17
    assert resolved["axes"][1]["pillar_context"]["pillar_id"] == 32
    assert resolved["axes"][2]["sector_context"]["sub_codes"] == [2]
    assert resolved["axes"][6]["crosswalk_context"]["crosswalk_type"] == "octopus"
    assert resolved["axes"][7]["crosswalk_context"]["crosswalk_type"] == "spiderweb"
    assert resolved["axes"][8]["role_context"]["role_type"] == "knowledge_role"
    assert resolved["axes"][12]["location_context"]["jurisdiction_level"] == 3
    assert resolved["axes"][13]["temporal_context"]["version"] == 1
    assert resolved["axes"][14]["acquisition_lifecycle_context"]["lifecycle_stage"] == "award"
    assert resolved["axes"][15]["risk_threat_context"]["risk_band"] == "critical"
    assert resolved["axes"][16]["ethics_trust_context"]["requires_human_review"]
    assert resolved["axes"][17]["frost_mode_context"]["tier"] == "autonomous"
    assert resolver.resolve_axis(AxisCoordinate(99, "1"))["axis_name"] == "Axis 99"
    assert [resolver._classify_risk_level(value) for value in (0, 2, 4, 6, 8)] == [
        "minimal",
        "low",
        "moderate",
        "high",
        "critical",
    ]


def test_crosswalk_traversal_honeycomb_octopus_spiderweb_and_deduplication(monkeypatch):
    traversal = CrosswalkTraversal()
    coordinate = UnifiedCoordinate()
    coordinate.set_axis(1, "32")
    coordinate.set_axis(3, "4.2")
    coordinate.set_axis(6, "1")
    coordinate.set_axis(7, "2")
    honeycomb = traversal.traverse_honeycomb(coordinate, 2)
    assert len(honeycomb) == 6
    assert traversal.traverse_octopus(coordinate)
    assert traversal.traverse_spiderweb(coordinate)
    dynamic = traversal.dynamic_traverse(coordinate, {"honeycomb_depth": 1})
    assert dynamic
    assert traversal.traversal_log
    assert traversal._deduplicate_coordinates([dynamic[0], dynamic[0]]) == [dynamic[0]]
    assert traversal._get_octopus_connections(999) == []
    assert traversal._get_spiderweb_connections(999) == []
    assert traversal.traverse_honeycomb(UnifiedCoordinate()) == []
    assert traversal.traverse_octopus(UnifiedCoordinate()) == []
    assert traversal.traverse_spiderweb(UnifiedCoordinate()) == []

    class Store:
        def cached_run_query(self, *_args, **_kwargs):
            return [{"props": {"code": "42", "sector_code": "54"}}]

    import backend.storage

    monkeypatch.setattr(backend.storage, "get_graph_store", lambda: Store())
    assert traversal._get_octopus_connections(7) == [{"pillar": "42", "sector": "54"}]


def test_unified_system_facade_creation_resolution_related_info_and_validation():
    system = create_coordinate_system()
    coordinate = system.create_coordinate(
        pillar="32.1",
        axis3="2.3",
        octopus="1",
        spiderweb={"value": "2", "meta_tag": "ISO", "description": "crosswalk"},
        ignored="value",
    )
    assert coordinate.get_dimension_count() == 4
    assert system.parse("1.2").get_axis(1).value == "2"
    assert system.resolve(coordinate)["dimension_count"] == 4
    assert system.traverse(coordinate)
    assert system.find_related(coordinate, [1])
    assert system.find_related(coordinate)
    assert system.get_axis_info(1)["category"] == "hierarchical_core"
    assert system.get_axis_info(6)["category"] == "crosswalk"
    assert system.get_axis_info(8)["category"] == "expert_role"
    assert system.get_axis_info(12)["category"] == "context"
    assert system.get_axis_info(14)["category"] == "extended_enterprise"
    with pytest.raises(ValueError):
        system.get_axis_info(18)
    validation = system.validate_coordinate(coordinate)
    assert validation["valid"]
    coordinate.coordinates[18] = AxisCoordinate(18, "")
    invalid = system.validate_coordinate(coordinate)
    assert not invalid["valid"]
    assert invalid["warnings"]
