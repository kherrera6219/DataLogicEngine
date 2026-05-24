from backend.storage.uskd_memory_graph import UskdMemoryGraph, get_uskd_memory_graph


def test_load_from_records_builds_graph_and_stats():
    graph = UskdMemoryGraph()

    stats = graph.load_from_records(
        pillars=[
            {
                "uid": "pillar-1",
                "pillar_id": "PL01",
                "name": "Healthcare",
                "description": "Healthcare regulations",
            }
        ],
        knowledge_nodes=[
            {
                "uid": "node-1",
                "node_id": "KN01",
                "title": "HIPAA Privacy Rule",
                "axis_number": 1,
                "content": "Patient privacy compliance",
            },
            {
                "uid": "node-2",
                "node_id": "KN02",
                "title": "Security Controls",
                "axis_number": 15,
                "content": "Threat and risk safeguards",
            },
        ],
        edges=[
            {
                "source_node_id": "node-1",
                "target_node_id": "node-2",
                "edge_type": "RELATED_TO",
                "weight": 0.75,
            }
        ],
    )

    assert stats.node_count == 3
    assert stats.edge_count == 1
    assert stats.pillar_count == 1
    assert stats.knowledge_node_count == 2

    matches = graph.search("privacy")
    assert [match["uid"] for match in matches] == ["node-1"]

    neighborhood = graph.neighborhood("node-1", depth=1)
    assert {node["uid"] for node in neighborhood["nodes"]} == {"node-1", "node-2"}
    assert neighborhood["edges"][0]["relationship_type"] == "RELATED_TO"


def test_load_from_neo4j_uses_graph_store_records():
    class FakeGraphStore:
        def run_query(self, query, parameters=None):
            if "RETURN labels(n)" in query:
                return [
                    {
                        "labels": ["Pillar"],
                        "props": {"uid": "pillar-1", "code": "PL01", "name": "Healthcare"},
                    },
                    {
                        "labels": ["KnowledgeNode"],
                        "props": {
                            "uid": "node-1",
                            "node_id": "KN01",
                            "title": "HIPAA",
                            "axis_number": 1,
                        },
                    },
                ]
            return [
                {
                    "source": {"uid": "pillar-1"},
                    "target": {"uid": "node-1"},
                    "rel_type": "HAS_KNOWLEDGE_NODE",
                    "props": {"weight": 1.0},
                }
            ]

    graph = UskdMemoryGraph()
    stats = graph.load_from_neo4j(FakeGraphStore())

    assert stats.node_count == 2
    assert stats.edge_count == 1
    assert graph.neighborhood("pillar-1")["edges"][0]["target"] == "node-1"


def test_singleton_returns_memory_graph_instance():
    graph = get_uskd_memory_graph()
    assert isinstance(graph, UskdMemoryGraph)


def test_upsert_authorized_knowledge_node_updates_existing_graph():
    graph = UskdMemoryGraph()
    graph.add_pillar("pillar-1", code="PL01", name="Healthcare")

    stats = graph.upsert_authorized_knowledge_node(
        "node-1",
        node_id="KN01",
        title="Approved knowledge",
        axis_number=1,
        pillar_uid="pillar-1",
    )

    assert stats.node_count == 2
    assert stats.edge_count == 1
    assert graph.coordinate_nodes(axis_number=1, text="approved")[0]["uid"] == "node-1"
