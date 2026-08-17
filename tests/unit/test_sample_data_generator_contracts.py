"""Deterministic contracts for local sample graph generation."""

import random

from core.simulation.data_generator import (
    distribute_nodes,
    generate_all_axis_data,
    generate_relationships,
    generate_sample_data,
)


class InMemoryDatabase:
    def __init__(self, fail_relationships=0):
        self.nodes = []
        self.relationships = {}
        self.fail_relationships = fail_relationships

    def add_node(self, **node):
        stored = {"node_id": f"node-{len(self.nodes) + 1}", **node}
        self.nodes.append(stored)
        return stored["node_id"]

    def get_nodes_by_axis(self, axis):
        return [node.copy() for node in self.nodes if node["axis"] == axis]

    def add_relationship(self, **relationship):
        if self.fail_relationships:
            self.fail_relationships -= 1
            raise RuntimeError("relationship rejected")
        relationship_id = f"rel-{len(self.relationships) + 1}"
        self.relationships[relationship_id] = {
            "relationship_id": relationship_id,
            **relationship,
        }
        return relationship_id

    def get_relationship(self, relationship_id):
        return self.relationships[relationship_id].copy()


def test_axis_distribution_preserves_total_and_priority():
    distribution = distribute_nodes(20, 13)
    assert sum(distribution.values()) == 20
    assert distribution[1] == 2
    assert distribution[11] == 2
    assert distribution[12] == 1

    remainder = distribute_nodes(25, 13)
    assert sum(remainder.values()) == 25
    assert remainder[4] == 2

    wide = distribute_nodes(30, 5)
    assert sum(wide.values()) == 30
    assert set(wide) == {1, 2, 3, 4, 5}


def test_generate_all_axis_data_populates_every_axis():
    random.seed(17)
    db = InMemoryDatabase()
    nodes = generate_all_axis_data(db, 39)

    assert set(nodes) == set(range(1, 14))
    assert len(nodes[1]) >= 5
    assert all(nodes[axis] for axis in range(1, 14))
    assert any(node["label"] == "Technology" for node in nodes[2])
    assert any("start_date" in node["attributes"] for node in nodes[13])

    expanded_db = InMemoryDatabase()
    expanded = generate_all_axis_data(expanded_db, 104)
    assert len(expanded[1]) > 5


def test_generate_relationships_structured_generic_duplicate_and_error_paths():
    random.seed(19)
    db = InMemoryDatabase(fail_relationships=1)
    nodes = generate_all_axis_data(db, 39)
    relationships = generate_relationships(db, nodes, 45)

    assert len(relationships) >= 45
    assert any(item["rel_type"] in {"related_to", "connected_with", "associated_with", "linked_to"} for item in relationships)

    sparse = {axis: [] for axis in range(1, 14)}
    sparse[1] = nodes[1]
    assert generate_relationships(InMemoryDatabase(), sparse, 0) == []


def test_generate_sample_data_returns_nodes_and_relationships():
    random.seed(23)
    db = InMemoryDatabase()
    nodes, relationships = generate_sample_data(db, num_nodes=39, num_relationships=20)
    assert sum(len(values) for values in nodes.values()) == len(db.nodes)
    assert len(relationships) >= 20
