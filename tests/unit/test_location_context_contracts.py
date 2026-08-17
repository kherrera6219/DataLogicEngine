"""Location resolution, hierarchy, filtering, and rule application contracts."""

from types import SimpleNamespace

from core.simulation.location_context_engine import LocationContextEngine


class GraphManager:
    def __init__(self, fail=False):
        self.fail = fail
        self.nodes = {
            "LOC_CITY": {"uid": "LOC_CITY", "node_type": "location", "name": "City", "level": "city"},
            "LOC_CUSTOM": {
                "uid": "LOC_CUSTOM",
                "node_type": "location",
                "name": "Custom",
                "level": "country",
                "attributes": {"linked_regulatory_framework_uids": ["REG-1", "REG-2"]},
            },
            "RULE": {"uid": "RULE", "node_type": "rule", "name": "Graph Rule", "priority": 1},
            "NOT_LOCATION": {"uid": "NOT_LOCATION", "node_type": "other"},
        }

    def get_node_by_uid(self, uid):
        if self.fail:
            raise RuntimeError("graph unavailable")
        return self.nodes.get(uid)

    def find_edges_by_properties(self, **properties):
        if self.fail:
            raise RuntimeError("edges unavailable")
        if properties.get("edge_type") == "contains_sub_location":
            parents = {"LOC_CITY": "LOC_STATE", "LOC_STATE": "LOC_COUNTRY_USA"}
            parent = parents.get(properties.get("target_uid"))
            return [{"source_uid": parent}] if parent else []
        if properties.get("edge_type") == "has_rule" and properties.get("source_uid") == "LOC_CITY":
            return [{"target_uid": "RULE"}, {}, {"target_uid": "NOT_LOCATION"}]
        return []


class NlpEngine:
    def extract_location(self, text, threshold):
        return {"location_id": "LOC_CITY", "name": text, "confidence": threshold}


class UnitedSystemManager:
    def __init__(self, component=None, fail=False):
        self.component = component
        self.fail = fail

    def get_component(self, name):
        if self.fail:
            raise RuntimeError("nlp unavailable")
        assert name == "nlp_engine"
        return self.component


def test_location_priority_hierarchy_cache_and_default_resolution():
    graph = GraphManager()
    engine = LocationContextEngine(graph_manager=graph)

    explicit = set(
        engine.determine_active_location_context(
            query_text="Canada", explicit_location_uids=["missing", "LOC_CITY"]
        )
    )
    assert explicit == {"LOC_CITY", "LOC_STATE", "LOC_COUNTRY_USA"}
    assert engine.stats["location_resolutions"] == 1
    assert engine.get_location_by_id("LOC_CITY")["name"] == "City"
    assert engine.stats["location_resolutions"] == 1

    query = engine.determine_active_location_context(query_text="Rules in Canada")
    assert query == ["LOC_COUNTRY_CAN"]
    profile = engine.determine_active_location_context(user_profile_location_uid="LOC_COUNTRY_GBR")
    assert profile == ["LOC_COUNTRY_GBR"]
    default = engine.determine_active_location_context(user_profile_location_uid="missing")
    assert default == ["LOC_COUNTRY_USA"]
    assert engine.get_default_location()["name"] == "United States"


def test_location_extraction_nlp_fallback_and_unknowns():
    nlp = LocationContextEngine(
        {"axis12_location_logic": {"location_extraction": {"use_nlp": True, "confidence_threshold": 0.88}}},
        united_system_manager=UnitedSystemManager(NlpEngine()),
    )
    assert nlp.extract_location("") is None
    assert nlp.extract_location("Seattle")["confidence"] == 0.88

    missing_component = LocationContextEngine(
        {"axis12_location_logic": {"location_extraction": {"use_nlp": True}}},
        united_system_manager=UnitedSystemManager(),
    )
    assert missing_component.extract_location("United Kingdom")["location_id"] == "LOC_COUNTRY_GBR"

    failing = LocationContextEngine(
        {"axis12_location_logic": {"location_extraction": {"use_nlp": True}}},
        united_system_manager=UnitedSystemManager(fail=True),
    )
    assert failing.extract_location("USA")["location_id"] == "LOC_COUNTRY_USA"
    assert failing.extract_location("Atlantis") is None
    assert failing.get_location_by_id("missing") is None


def test_location_regulations_filter_rules_and_application():
    engine = LocationContextEngine(graph_manager=GraphManager())
    regs = set(engine.get_applicable_regulations_for_locations(["missing", "LOC_CUSTOM"]))
    assert regs == {"REG-1", "REG-2"}

    nodes = [
        {"id": "global", "attributes": {}},
        {"id": "usa", "attributes": {"applicable_locations": ["LOC_COUNTRY_USA"]}},
        {"id": "uk", "attributes": {"applicable_locations": ["LOC_COUNTRY_GBR"]}},
    ]
    assert engine.filter_nodes_by_location_context(nodes, []) is nodes
    assert [item["id"] for item in engine.filter_nodes_by_location_context(nodes, ["LOC_COUNTRY_USA"])] == [
        "global",
        "usa",
    ]

    graph_rules = engine.get_location_rules("LOC_CITY")
    assert [rule["uid"] for rule in graph_rules] == ["RULE"]
    assert len(engine.get_location_rules()) == 2
    assert len(engine.get_location_rules("LOC_COUNTRY_GBR")) == 1
    assert engine.get_location_rules("LOC_COUNTRY_CAN") == []

    applied = engine.apply_location_context({"personal_data": "value"})
    assert applied["_location_context"]["name"] == "United States"
    assert "personal_data_note" in applied
    assert "regulatory_note" in applied
    assert len(applied["_applied_rules"]) == 2
    assert engine.stats["rule_applications"] == 2

    unknown_rule = engine._apply_rule({}, {"uid": "custom", "name": "Custom", "rule_type": "other"})
    assert unknown_rule["_applied_rules"][0]["rule_id"] == "custom"


def test_location_graph_failures_use_built_in_fallbacks_and_basic_default():
    engine = LocationContextEngine(
        {"axis12_location_logic": {"default_location_context_uid": "LOC_UNKNOWN"}},
        graph_manager=GraphManager(fail=True),
    )
    assert engine.get_location_by_id("LOC_COUNTRY_USA")["name"] == "United States"
    assert engine.get_location_rules("LOC_COUNTRY_USA")[0]["uid"] == "RULE_USA_01"
    assert engine.get_default_location() == {
        "uid": "LOC_UNKNOWN",
        "name": "Default Location",
        "level": "country",
    }
    assert engine.apply_location_context({"value": 1}, "LOC_UNKNOWN")["_location_context"]["name"] == "Default Location"


def test_location_hierarchy_stops_cycles():
    class CyclicGraph:
        def find_edges_by_properties(self, **properties):
            target = properties["target_uid"]
            return [{"source_uid": "b" if target == "a" else "a"}]

    engine = LocationContextEngine(graph_manager=CyclicGraph())
    assert set(engine._expand_location_hierarchy(["a"])) == {"a", "b"}
