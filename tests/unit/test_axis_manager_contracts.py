"""In-memory behavioral contracts for the legacy graph axis managers."""

from datetime import datetime

from core.axes.axis2_sector import SectorManager
from core.axes.axis3_honeycomb import HoneycombSystem
from core.axes.axis4_branch import BranchManager
from core.axes.axis6_regulatory import RegulatoryManager
from core.axes.axis7_compliance import ComplianceManager, LegacyComplianceManager


class MemoryDB:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.fail = False

    def add_node(self, data):
        if self.fail:
            raise RuntimeError("database failed")
        node = dict(data)
        node.setdefault("uid", f"node-{len(self.nodes) + 1}")
        node.setdefault("id", node["uid"])
        self.nodes[node["uid"]] = node
        return node

    def add_edge(self, data):
        if self.fail:
            raise RuntimeError("database failed")
        edge = dict(data)
        edge.setdefault("uid", f"edge-{len(self.edges) + 1}")
        self.edges.append(edge)
        return edge

    def get_node(self, uid):
        return self.nodes.get(uid)

    def get_node_by_id(self, node_id):
        return next((node for node in self.nodes.values() if node.get("id") == node_id), None)

    def get_nodes_by_properties(self, properties, limit=None):
        found = [
            node
            for node in self.nodes.values()
            if all(node.get(key) == value for key, value in properties.items())
        ]
        return found[:limit] if limit is not None else found

    def get_edges_between(self, source_uid, target_uid, edge_types=None):
        return [
            edge
            for edge in self.edges
            if edge.get("source_id") == source_uid
            and edge.get("target_id") == target_uid
            and (not edge_types or edge.get("edge_type") in edge_types)
        ]

    def get_outgoing_edges(self, uid, edge_types=None):
        return [
            edge
            for edge in self.edges
            if edge.get("source_id") == uid
            and (not edge_types or edge.get("edge_type") in edge_types)
        ]

    def get_incoming_edges(self, uid, edge_types=None):
        return [
            edge
            for edge in self.edges
            if edge.get("target_id") == uid
            and (not edge_types or edge.get("edge_type") in edge_types)
        ]


class GraphAdapter:
    def __init__(self, db):
        self.db = db

    def add_node(self, data):
        return {"status": "success", "node": self.db.add_node(data)}

    def add_edge(self, data):
        return {"status": "success", "edge": self.db.add_edge(data)}

    def get_outgoing_edges(self, uid, edge_types=None):
        return self.db.get_outgoing_edges(uid, edge_types)


def add(db, uid, node_type, **extra):
    return db.add_node({"uid": uid, "id": extra.pop("id", uid), "node_type": node_type, **extra})


def test_sector_registration_mapping_hierarchy_and_related_contracts():
    db = MemoryDB()
    manager = SectorManager(db, db)
    assert SectorManager().register_sector({})["status"] == "error"
    assert manager.register_sector({"label": "Missing"})["status"] == "error"
    first = manager.register_sector(
        {"label": "Technology", "classification_system": "naics", "code": "51"}
    )["sector"]
    child = manager.register_sector(
        {"label": "Software", "classification_system": "naics", "code": "5112"}
    )["sector"]
    sic = manager.register_sector(
        {"label": "Software SIC", "classification_system": "sic", "code": "7372"}
    )["sector"]
    assert manager.register_sector(
        {"label": "Duplicate", "classification_system": "naics", "code": "51"}
    )["status"] == "exists"
    assert manager.get_sector_by_code("unknown", "1")["status"] == "error"
    assert manager.get_sector_by_code("naics", "none")["status"] == "not_found"
    assert manager.get_sector_by_code("NAICS", "51")["sector"] == first

    hierarchy = manager.establish_sector_hierarchy(first["uid"], child["uid"])
    assert hierarchy["status"] == "success"
    assert manager.establish_sector_hierarchy(first["uid"], child["uid"])["status"] == "exists"
    assert manager.establish_sector_hierarchy("missing", child["uid"])["status"] == "error"
    assert manager.get_sector_hierarchy(child["uid"], "up", 3)["hierarchy_count"] == 1
    assert manager.get_sector_hierarchy(first["uid"], "down", 3)["hierarchy_count"] == 1

    mapping = manager.map_between_classifications("naics", "5112", "sic", "7372")
    assert mapping["status"] == "success"
    assert manager.map_between_classifications("naics", "5112", "sic", "7372")["status"] == "exists"
    assert manager.map_between_classifications("naics", "missing", "sic", "7372")["status"] == "error"
    related = manager.find_related_sectors(child["uid"], max_distance=3)
    assert related["status"] == "success"
    assert related["related_count"] >= 2
    assert manager.find_related_sectors("missing")["status"] == "error"

    db.fail = True
    assert manager.register_sector(
        {"label": "Failure", "classification_system": "naics", "code": "0"}
    )["status"] == "error"


def test_honeycomb_connections_crosswalk_paths_and_multi_axis_generation():
    db = MemoryDB()
    graph = GraphAdapter(db)
    manager = HoneycombSystem(db, graph)
    assert HoneycombSystem().create_honeycomb_connection("a", "b", "related")["status"] == "error"
    sector = add(db, "sector", "sector", id="51", code="51", name="Technology")
    pillar = add(
        db,
        "pillar",
        "pillar_level",
        pillar_id="PL03",
        name="Formal Sciences",
        sublevels={
            "level_1": [{"id": "sub1"}, {"id": None}],
            "level_2": [{"id": "sub2", "parent": "sub1"}],
        },
    )
    add(db, "sub-one", "pillar_level", id="sub1")
    add(db, "sub-two", "pillar_level", id="sub2")
    other = add(db, "other", "concept", axis_number=4)

    created = manager.create_honeycomb_connection("sector", "pillar", "implements", 0.8)
    assert created["status"] == "success"
    assert manager.create_honeycomb_connection("sector", "pillar", "implements", 0.8)["status"] == "exists"
    assert manager.create_honeycomb_connection("missing", "pillar", "implements")["status"] == "error"
    assert manager.create_honeycomb_connection("sector", "other", "implements", 2)["status"] == "success"
    assert manager._determine_pillar_sector_connection(pillar, sector) == ("direct_application", 0.9)
    assert manager._determine_pillar_sector_connection(
        {"name": "Technology"}, {"code": "0", "name": "Technology"}
    )[1] == 0.8
    assert manager._determine_pillar_sector_connection(
        {"name": "Universal Foundation"}, {"code": "0", "name": "Other"}
    )[1] == 0.7

    crosswalk = manager.generate_sector_pillar_crosswalk("51")
    assert crosswalk["status"] == "success"
    assert crosswalk["connection_count"] >= 3
    assert manager.generate_sector_pillar_crosswalk("missing")["status"] == "error"
    manager.create_honeycomb_connection("pillar", "other", "crosswalks_to", 0.5)
    paths = manager.find_crosswalk_paths("sector", "other", 3)
    assert paths["status"] == "success"
    assert paths["path_count"] >= 1
    assert manager._find_all_paths("sector", "sector", 1) == [["sector"]]
    assert manager.find_crosswalk_paths("missing", "other")["status"] == "error"

    generated = manager.generate_multi_axis_honeycomb("sector", max_connections=2)
    assert generated["status"] == "success"
    assert generated["connection_count"] <= 2
    assert manager.generate_multi_axis_honeycomb("missing")["status"] == "error"
    assert sector and other


def test_branch_domains_concepts_relations_paths_and_taxonomy():
    db = MemoryDB()
    manager = BranchManager(db, db)
    assert BranchManager().create_domain({})["status"] == "error"
    assert manager.create_domain({"label": "No description"})["status"] == "error"
    domain = manager.create_domain({"label": "AI", "description": "Artificial intelligence"})["domain"]
    assert manager.create_domain({"label": "AI", "description": "again"})["status"] == "exists"
    parent = manager.create_concept({"label": "Learning", "domain_uid": domain["uid"]})["concept"]
    child = manager.create_concept({"label": "Deep Learning", "domain_uid": domain["uid"]})["concept"]
    leaf = manager.create_concept({"label": "Transformer", "domain_uid": domain["uid"]})["concept"]
    assert manager.create_concept({"label": "Bad", "domain_uid": "missing"})["status"] == "error"
    assert manager.create_concept({"label": "Learning", "domain_uid": domain["uid"]})["status"] == "exists"
    assert manager.relate_concepts(parent["uid"], child["uid"], "broader")["status"] == "success"
    assert manager.relate_concepts(child["uid"], leaf["uid"], "broader")["status"] == "success"
    assert manager.relate_concepts(parent["uid"], leaf["uid"], "invalid")["status"] == "error"
    assert manager.relate_concepts(parent["uid"], child["uid"], "broader")["status"] == "exists"

    concepts = manager.get_domain_concepts(domain["uid"])
    assert concepts["concept_count"] == 3
    relations = manager.get_concept_relations(child["uid"], ["broader", "narrower"])
    assert relations["outgoing_count"] + relations["incoming_count"] >= 2
    assert manager.get_concept_relations(child["uid"], ["invalid"])["status"] == "error"
    path = manager.find_concept_path(parent["uid"], leaf["uid"], ["broader"], 3)
    assert path["status"] == "success"
    assert path["path_count"] >= 1
    assert manager.find_concept_path(parent["uid"], leaf["uid"], ["invalid"], 3)["status"] == "error"
    taxonomy = manager.extract_concept_taxonomy(parent["uid"], "broader", 3)
    assert taxonomy["status"] == "success"
    assert taxonomy["taxonomy_tree"]["concept"]["uid"] == parent["uid"]


def framework(label):
    return {
        "label": label,
        "framework_type": "regulation",
        "issuing_authority": "Authority",
        "effective_date": datetime(2026, 1, 1),
        "expiration_date": datetime(2030, 1, 1),
    }


def test_regulatory_octopus_links_jurisdictions_crosswalk_and_compliance():
    db = MemoryDB()
    manager = RegulatoryManager(db, db)
    assert RegulatoryManager().create_mega_framework(framework("missing db"))["status"] == "error"
    assert manager.create_mega_framework({"label": "missing"})["status"] == "error"
    assert manager.create_mega_framework(
        {"label": "custom", "framework_type": "custom", "issuing_authority": "A"}
    )["status"] == "warning"
    mega = manager.create_mega_framework(framework("Mega"))["framework"]
    large = manager.create_large_framework(framework("Large"), mega["uid"])["framework"]
    medium = manager.create_medium_framework(framework("Medium"), large["uid"])["framework"]
    small = manager.create_small_framework(framework("Small"), medium["uid"])["framework"]
    requirement = manager.create_granular_requirement({"label": "Encrypt data"}, small["uid"])["requirement"]
    assert manager._link_parent_child_frameworks(mega["uid"], large["uid"], "has_large_framework")["status"] == "exists"
    octopus = manager.get_octopus_structure(mega["uid"])
    assert octopus["status"] == "success"
    assert octopus["octopus"]["mega_framework"] == mega
    assert manager.get_octopus_structure(large["uid"])["status"] == "error"

    second = manager.create_mega_framework(framework("Second"))["framework"]
    assert manager.link_regulatory_frameworks(mega["uid"], second["uid"], "references")["status"] == "success"
    assert manager.link_regulatory_frameworks(mega["uid"], second["uid"], "references")["status"] == "exists"
    assert manager.link_regulatory_frameworks(mega["uid"], second["uid"], "custom")["status"] == "warning"
    jurisdiction = manager.map_jurisdictions(
        mega["uid"], {"type": "national", "name": "United States", "code": "US"}
    )
    assert jurisdiction["status"] == "success"
    assert manager.map_jurisdictions(mega["uid"], {"type": "invalid", "name": "x"})["status"] == "warning"
    assert manager.map_jurisdictions("missing", {"type": "national", "name": "x"})["status"] == "error"

    crosswalk = manager.create_regulatory_crosswalk(large["uid"], second["uid"], "equivalent_to")
    assert crosswalk["status"] == "success"
    assert manager.create_regulatory_crosswalk(large["uid"], second["uid"], "equivalent_to")["status"] == "exists"
    compliance = add(db, "compliance", "compliance_standard", axis_number=7)
    assert manager.create_compliance_link(mega["uid"], compliance["uid"], "implements")["status"] == "success"
    assert manager.create_compliance_link(mega["uid"], compliance["uid"], "implements")["status"] == "exists"
    assert requirement


def test_legacy_compliance_standard_control_assessment_and_equivalence():
    db = MemoryDB()
    manager = LegacyComplianceManager(db, db)
    regulatory = add(db, "reg", "regulatory_framework")
    standard = manager.create_compliance_standard(
        {
            "label": "ISO 27001",
            "standard_type": "international",
            "issuing_authority": "ISO",
            "related_regulatory_framework_uid": regulatory["uid"],
            "effective_date": datetime(2026, 1, 1),
        }
    )["standard"]
    assert manager.create_compliance_standard({"label": "bad"})["status"] == "error"
    assert manager.create_compliance_standard(
        {"label": "custom", "standard_type": "custom", "issuing_authority": "A"}
    )["status"] == "warning"
    control = manager.create_compliance_control(
        {
            "label": "Access control",
            "standard_uid": standard["uid"],
            "control_category": "technical",
            "description": "Restrict access",
        }
    )["control"]
    other = manager.create_compliance_control(
        {
            "label": "Identity control",
            "standard_uid": standard["uid"],
            "control_category": "administrative",
            "description": "Manage identity",
        }
    )["control"]
    assert manager.create_compliance_control(
        {"label": "bad", "standard_uid": "missing", "control_category": "technical", "description": "x"}
    )["status"] == "error"
    assert manager.map_control_to_control(control["uid"], other["uid"], "subset_of")["status"] == "success"
    assert manager.map_control_to_control(control["uid"], other["uid"], "subset_of")["status"] == "exists"
    assert manager.map_control_to_control(control["uid"], other["uid"], "custom")["status"] == "warning"
    requirement = add(db, "requirement", "regulatory_requirement")
    assert manager.link_control_to_regulatory_requirement(
        control["uid"], requirement["uid"], "implements"
    )["status"] == "success"
    assert manager.link_control_to_regulatory_requirement(
        control["uid"], requirement["uid"], "implements"
    )["status"] == "exists"
    assessment = manager.create_compliance_assessment(
        {"standard_uid": standard["uid"], "entity_name": "ACME", "status": "completed"}
    )["assessment"]
    result = manager.add_assessment_result(
        assessment["uid"], control["uid"], {"status": "compliant", "details": "passed"}
    )
    assert result["status"] == "success"
    details = manager.get_standard_details(standard["uid"], True, True)
    assert details["status"] == "success"
    assert details["control_count"] == 2
    equivalent = manager.find_equivalent_controls(control["uid"], 3)
    assert equivalent["status"] == "success"
    assert equivalent["equivalent_count"] >= 1


def test_spiderweb_compliance_hierarchy_mapping_and_sector_lookup():
    db = MemoryDB()
    graph = GraphAdapter(db)
    manager = ComplianceManager(db, graph)
    assert ComplianceManager().register_compliance_standard({})["status"] == "error"
    mega = manager.register_compliance_standard(
        {"label": "ISO", "standard_level": "mega", "standard_type": "iso", "id": "iso"}
    )["standard"]
    large = manager.register_compliance_standard(
        {"label": "ISO 27001", "standard_level": "large", "standard_type": "iso", "id": "iso27001"},
        "iso",
    )["standard"]
    medium = manager.register_compliance_standard(
        {"label": "Security", "standard_level": "medium", "standard_type": "iso", "id": "security"},
        "iso27001",
    )["standard"]
    small = manager.register_compliance_standard(
        {"label": "Access", "standard_level": "small", "standard_type": "iso", "id": "access"},
        "security",
    )["standard"]
    manager.register_compliance_standard(
        {"label": "Access point", "standard_level": "granular", "standard_type": "iso", "id": "access-point"},
        "access",
    )
    assert manager.register_compliance_standard(
        {"label": "ISO", "standard_level": "mega", "standard_type": "iso"}
    )["status"] == "exists"
    assert manager.register_compliance_standard(
        {"label": "bad", "standard_level": "wrong", "standard_type": "iso"}
    )["status"] == "error"
    hierarchy = manager.get_compliance_hierarchy("iso")
    assert hierarchy["status"] == "success"
    assert hierarchy["total_standards"] == 1

    regulatory = add(db, "regulatory", "regulatory_framework", framework_level="large")
    mapping = manager.map_regulatory_to_compliance(regulatory["uid"], large["uid"])
    assert mapping["status"] == "success"
    assert manager.map_regulatory_to_compliance(regulatory["uid"], large["uid"])["status"] == "exists"
    sector = add(db, "sector", "sector", id="technology")
    db.add_edge(
        {"source_id": sector["uid"], "target_id": large["uid"], "edge_type": "complies_with", "attributes": {"confidence": 0.95}}
    )
    db.add_edge(
        {"source_id": sector["uid"], "target_id": regulatory["uid"], "edge_type": "regulated_by", "attributes": {}}
    )
    db.add_edge(
        {"source_id": regulatory["uid"], "target_id": small["uid"], "edge_type": "implements", "attributes": {"confidence": 0.8}}
    )
    found = manager.find_compliance_for_sector("technology", "iso")
    assert found["status"] == "success"
    assert found["standard_count"] == 2
    assert manager.find_compliance_for_sector("missing")["status"] == "error"
    assert mega and medium
