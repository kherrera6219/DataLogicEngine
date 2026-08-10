"""Index SQL KnowledgeGraphNode rows into the Chroma knowledge_nodes collection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


@dataclass
class IndexResult:
    scanned: int = 0
    indexed: int = 0
    skipped: int = 0

    def to_dict(self) -> dict[str, int]:
        return {"scanned": self.scanned, "indexed": self.indexed, "skipped": self.skipped}


def _node_identifier(node) -> str:
    return str(node.uid or node.node_id or f"sql-{node.id}")


def _node_text(node) -> str:
    parts = [
        node.title,
        node.label,
        node.description,
        node.content,
    ]
    return "\n\n".join(str(part).strip() for part in parts if str(part or "").strip())


def _node_metadata(node) -> dict:
    return {
        "sql_id": node.id,
        "uid": node.uid or "",
        "node_id": node.node_id or "",
        "node_type": node.node_type or "knowledge_node",
        "axis_number": node.axis_number or 0,
        "tenant_id": node.tenant_id or "",
        "title": node.title or node.label or "",
        "source": "ukg_knowledge_nodes",
    }


def index_nodes(nodes: Iterable, rag_service=None) -> IndexResult:
    """Index provided KnowledgeGraphNode-like objects into RAG."""
    if rag_service is None:
        from backend.services.rag_service import get_rag_service

        rag_service = get_rag_service()

    result = IndexResult()
    for node in nodes:
        result.scanned += 1
        text = _node_text(node)
        if not text:
            result.skipped += 1
            continue
        ok = rag_service.ingest_knowledge_node(
            _node_identifier(node),
            text,
            node.node_type or "knowledge_node",
            _node_metadata(node),
        )
        if ok:
            result.indexed += 1
        else:
            result.skipped += 1
    return result


def index_from_database(limit: int | None = None, *, flask_app=None) -> IndexResult:
    """Load KnowledgeGraphNode rows through Flask SQLAlchemy and index them."""
    from models import KnowledgeGraphNode

    if flask_app is None:
        import app as app_module

        flask_app = app_module.app

    with flask_app.app_context():
        query = KnowledgeGraphNode.query.order_by(KnowledgeGraphNode.id.asc())
        if limit:
            query = query.limit(limit)
        return index_nodes(query.all())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of SQL nodes to index.")
    args = parser.parse_args()

    result = index_from_database(limit=args.limit)
    print(result.to_dict())
    return 0 if result.scanned == result.indexed + result.skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
