"""In-memory and delegated contracts for the core graph manager facade."""

from core.graph.graph_manager import GraphManager


class DB:
    def __init__(self):
        self.nodes = {
            "a": {"uid": "a", "node_type": "concept", "label": "A"},
            "b": {"uid": "b", "node_type": "concept", "label": "B"},
        }
        self.edges = {"e": {"uid": "e", "edge_type": "related", "source_uid": "a", "target_uid": "b"}}
        self.fail = set()

    def get_node_by_uid(self, uid): return self.nodes.get(uid)
    def get_edge_by_uid(self, uid): return self.edges.get(uid)
    def create_node(self, data):
        if "create_node" in self.fail: return None
        self.nodes[data["uid"]] = dict(data); return self.nodes[data["uid"]]
    def update_node(self, uid, updates):
        if "update_node" in self.fail or uid not in self.nodes: return None
        self.nodes[uid] = {**self.nodes[uid], **updates}; return self.nodes[uid]
    def delete_node(self, uid):
        if "delete_node" in self.fail: return False
        return self.nodes.pop(uid, None) is not None
    def create_edge(self, data):
        if "create_edge" in self.fail: return None
        self.edges[data["uid"]] = dict(data); return self.edges[data["uid"]]
    def update_edge(self, uid, updates):
        if "update_edge" in self.fail or uid not in self.edges: return None
        self.edges[uid] = {**self.edges[uid], **updates}; return self.edges[uid]
    def delete_edge(self, uid):
        if "delete_edge" in self.fail: return False
        return self.edges.pop(uid, None) is not None
    def get_nodes_by_type(self, node_type, limit, offset):
        return [n for n in self.nodes.values() if n.get("node_type") == node_type][offset:offset + limit]
    def get_edges_by_type(self, edge_type, limit, offset):
        return [e for e in self.edges.values() if e.get("edge_type") == edge_type][offset:offset + limit]
    def get_outgoing_edges(self, uid): return [e for e in self.edges.values() if e.get("source_uid") == uid]
    def get_incoming_edges(self, uid): return [e for e in self.edges.values() if e.get("target_uid") == uid]
    def search_nodes(self, query, node_types, axis_numbers, limit):
        return [n for n in self.nodes.values() if query.lower() in n.get("label", "").lower()][:limit]
    def get_neighbors(self, uid, edge_types, direction, max_depth):
        return {"nodes": list(self.nodes.values()), "edges": list(self.edges.values())}


def test_database_backed_node_and_edge_lifecycle_and_indexes():
    db = DB()
    manager = GraphManager({"graph_manager": {"cache": True}})
    manager.set_db_manager(db)
    assert manager.get_node_by_uid("a")["label"] == "A"
    assert manager.get_node_by_uid("a")["uid"] == "a"
    assert manager.get_node_by_uid("missing") is None
    assert manager.get_edge_by_uid("e")["edge_type"] == "related"
    assert manager.get_edge_by_uid("e")["uid"] == "e"
    assert manager.get_edge_by_uid("missing") is None

    node = manager.create_node("sector", "Technology", "desc", {"code": "51"}, uid="sector", axis_number=2, level=1)
    assert node["attributes"]["code"] == "51"
    assert manager.update_node("sector", {"label": "Tech"})["label"] == "Tech"
    edge = manager.create_edge("maps", "a", "b", "mapping", 0.8, {"confidence": 1}, uid="map")
    assert edge["weight"] == 0.8
    assert manager.create_edge("maps", "missing", "b") is None
    assert manager.create_edge("maps", "a", "missing") is None
    assert manager.update_edge("map", {"weight": 0.9})["weight"] == 0.9
    assert manager.delete_edge("map")
    assert manager.delete_node("sector")
    assert manager.stats["nodes_created"] == 1
    assert manager.stats["edges_created"] == 1


def test_database_query_facades_populate_caches_and_stats():
    db = DB()
    manager = GraphManager()
    manager.set_db_manager(db)
    assert len(manager.get_nodes_by_type("concept")) == 2
    assert len(manager.get_edges_by_type("related")) == 1
    assert len(manager.get_outgoing_edges("a")) == 1
    assert len(manager.get_incoming_edges("b")) == 1
    assert manager.search_nodes("A")[0]["uid"] == "a"
    neighbors = manager.get_neighbors("a", ["related"], "both", 2)
    assert len(neighbors["nodes"]) == 2
    stats = manager.get_stats()
    assert stats["queries_executed"] == 1
    assert stats["cache_stats"]["nodes_cached"] == 2
    assert stats["cache_stats"]["edges_cached"] == 1


def test_database_failures_return_bounded_results():
    db = DB()
    manager = GraphManager()
    manager.set_db_manager(db)
    for operation in ("create_node", "update_node", "delete_node", "create_edge", "update_edge", "delete_edge"):
        db.fail = {operation}
        if operation == "create_node": assert manager.create_node("x", "x", uid="x") is None
        elif operation == "update_node": assert manager.update_node("a", {}) is None
        elif operation == "delete_node": assert not manager.delete_node("a")
        elif operation == "create_edge": assert manager.create_edge("x", "a", "b", uid="x") is None
        elif operation == "update_edge": assert manager.update_edge("e", {}) is None
        else: assert not manager.delete_edge("e")


def test_cache_only_mode_updates_queries_and_deletes_locally():
    manager = GraphManager()
    transient = manager.create_node("concept", "Transient", uid="transient")
    assert transient["uid"] == "transient"
    manager.node_cache["transient"] = transient
    manager.node_type_index["concept"] = ["transient", "missing"]
    assert manager.update_node("transient", {"label": "Updated"})["label"] == "Updated"
    assert manager.update_node("missing", {}) is None
    assert manager.get_nodes_by_type("concept") == [manager.node_cache["transient"]]
    assert manager.get_node_by_uid("absent") is None

    manager.node_cache["target"] = {"uid": "target", "node_type": "concept"}
    edge = manager.create_edge("related", "transient", "target", uid="local-edge")
    assert edge["uid"] == "local-edge"
    manager.edge_cache["local-edge"] = edge
    manager.edge_type_index["related"] = ["local-edge", "missing"]
    assert manager.update_edge("local-edge", {"weight": 2})["weight"] == 2
    assert manager.update_edge("missing", {}) is None
    assert manager.get_edges_by_type("related") == [manager.edge_cache["local-edge"]]
    assert manager.get_edge_by_uid("absent") is None
    assert manager.get_outgoing_edges("transient") == []
    assert manager.get_incoming_edges("target") == []
    assert manager.search_nodes("Updated") == []
    assert manager.get_neighbors("transient") == {"nodes": [], "edges": []}
    assert manager.delete_edge("local-edge")
    assert not manager.delete_edge("missing")
    assert manager.delete_node("transient")
    assert not manager.delete_node("missing")
