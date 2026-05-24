"""Sync SQL knowledge nodes into Neo4j KnowledgeNode nodes.

Usage:
    python scripts/sync_nodes_to_neo4j.py [--limit 100]

The sync is idempotent: KnowledgeNode rows are merged by uid, and graph edges are
merged by source/target uid or node_id when both endpoints can be resolved.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import app  # noqa: E402
from extensions import db  # noqa: E402
from models import KnowledgeGraphEdge, KnowledgeGraphNode  # noqa: E402
from backend.storage import get_graph_store, get_uskd_memory_graph  # noqa: E402


def _node_uid(node: KnowledgeGraphNode) -> str:
    return str(node.uid or node.node_id or node.id)


def _node_props(node: KnowledgeGraphNode) -> dict[str, Any]:
    return {
        "uid": _node_uid(node),
        "node_id": node.node_id,
        "node_type": node.node_type,
        "label": node.label,
        "title": node.title,
        "description": node.description,
        "content": node.content,
        "content_type": node.content_type,
        "axis_number": node.axis_number,
        "tenant_id": node.tenant_id,
    }


def sync(limit: int | None = None) -> dict[str, int]:
    store = get_graph_store()
    store.connect()
    if not store.driver:
        raise RuntimeError("Could not connect to Neo4j. Is it running?")

    with app.app_context():
        from sqlalchemy import inspect

        bind = db.session.get_bind()
        table_names = set(inspect(bind).get_table_names())
        required_tables = {KnowledgeGraphNode.__tablename__, KnowledgeGraphEdge.__tablename__}
        if not required_tables.issubset(table_names):
            missing = ", ".join(sorted(required_tables - table_names))
            return {
                "sql_nodes": 0,
                "sql_edges": 0,
                "merged_nodes": 0,
                "merged_edges": 0,
                "memory_nodes": get_uskd_memory_graph().stats().node_count,
                "memory_edges": get_uskd_memory_graph().stats().edge_count,
                "skipped_missing_tables": missing,
            }

        query = KnowledgeGraphNode.query.order_by(KnowledgeGraphNode.id)
        if limit:
            query = query.limit(limit)
        nodes = query.all()
        edges = KnowledgeGraphEdge.query.all()

        id_by_node_id = {node.node_id: _node_uid(node) for node in nodes if node.node_id}

        merged_nodes = 0
        for node in nodes:
            if store.merge_knowledge_node(_node_props(node)):
                merged_nodes += 1

        merged_edges = 0
        for edge in edges:
            source_uid = id_by_node_id.get(edge.source_node_id)
            target_uid = id_by_node_id.get(edge.target_node_id)
            if not source_uid or not target_uid:
                continue
            if store.merge_relationship_by_uid(
                source_uid,
                target_uid,
                edge.edge_type or "RELATED_TO",
                {"edge_id": edge.edge_id, "weight": edge.weight, "data": edge.data},
            ):
                merged_edges += 1

        memory_stats = get_uskd_memory_graph().load_from_records(
            knowledge_nodes=nodes,
            edges=edges,
        )

    return {
        "sql_nodes": len(nodes),
        "sql_edges": len(edges),
        "merged_nodes": merged_nodes,
        "merged_edges": merged_edges,
        "memory_nodes": memory_stats.node_count,
        "memory_edges": memory_stats.edge_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync SQL knowledge nodes to Neo4j")
    parser.add_argument("--limit", type=int, default=None, help="Optional max nodes to sync")
    args = parser.parse_args()

    try:
        result = sync(limit=args.limit)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    if result.get("skipped_missing_tables"):
        print(f"Skipped SQL-to-Neo4j sync; missing SQL tables: {result['skipped_missing_tables']}")
        return 0

    print(
        "Synced SQL-to-Neo4j: "
        f"{result['merged_nodes']}/{result['sql_nodes']} nodes, "
        f"{result['merged_edges']}/{result['sql_edges']} edges; "
        f"memory graph={result['memory_nodes']} nodes/{result['memory_edges']} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
