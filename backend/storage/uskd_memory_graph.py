"""In-memory USKD graph backed by NetworkX.

The persistent knowledge graph lives in SQLite/PostgreSQL and Neo4j. This module
provides the RAM-resident graph that reasoning layers can query without paying a
database round trip for every traversal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import logging
from typing import Any, Iterable, Mapping, Optional

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UskdGraphStats:
    """Lightweight graph health summary."""

    node_count: int
    edge_count: int
    pillar_count: int
    knowledge_node_count: int
    last_loaded_at: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "pillar_count": self.pillar_count,
            "knowledge_node_count": self.knowledge_node_count,
            "last_loaded_at": self.last_loaded_at,
        }


@dataclass
class UskdMemoryGraph:
    """NetworkX-backed in-memory representation of the active USKD graph."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    last_loaded_at: Optional[datetime] = None

    def clear(self) -> None:
        self.graph.clear()
        self.last_loaded_at = None

    def load_from_records(
        self,
        *,
        pillars: Iterable[Any] = (),
        knowledge_nodes: Iterable[Any] = (),
        edges: Iterable[Any] = (),
        clear_existing: bool = True,
    ) -> UskdGraphStats:
        """Load records from SQLAlchemy models, dictionaries, or test doubles."""
        if clear_existing:
            self.graph.clear()

        for pillar in pillars:
            data = self._record_to_mapping(pillar)
            node_key = self._first_present(data, "uid", "pillar_id", "id")
            if not node_key:
                continue
            self.add_pillar(
                str(node_key),
                code=self._optional_str(data.get("pillar_id")),
                name=self._optional_str(data.get("name")),
                data=data,
            )

        for node in knowledge_nodes:
            data = self._record_to_mapping(node)
            node_key = self._first_present(data, "uid", "node_id", "id")
            if not node_key:
                continue
            self.add_knowledge_node(
                str(node_key),
                node_id=self._optional_str(data.get("node_id")),
                title=self._optional_str(data.get("title") or data.get("label")),
                axis_number=data.get("axis_number"),
                data=data,
            )

            pillar_uid = data.get("pillar_level_id") or data.get("pillar_uid")
            if pillar_uid and self.graph.has_node(str(pillar_uid)):
                self.add_relationship(str(pillar_uid), str(node_key), "HAS_KNOWLEDGE_NODE")

        for edge in edges:
            data = self._record_to_mapping(edge)
            source = self._first_present(data, "source_node_id", "source_id", "source")
            target = self._first_present(data, "target_node_id", "target_id", "target")
            if not source or not target:
                continue
            self.add_relationship(
                str(source),
                str(target),
                self._optional_str(data.get("edge_type")) or "RELATED_TO",
                weight=data.get("weight"),
                data=data,
            )

        self.last_loaded_at = datetime.now(UTC)
        return self.stats()

    def load_from_neo4j(self, graph_store: Any) -> UskdGraphStats:
        """Load Pillar and KnowledgeNode data from a GraphStore-like object."""
        records = graph_store.run_query(
            """
            MATCH (n)
            WHERE n:Pillar OR n:KnowledgeNode
            RETURN labels(n) AS labels, properties(n) AS props
            """
        )
        if not records:
            logger.info("Neo4j returned no USKD records; retaining existing memory graph")
            return self.stats()

        rel_records = graph_store.run_query(
            """
            MATCH (a)-[r]->(b)
            WHERE (a:Pillar OR a:KnowledgeNode) AND (b:Pillar OR b:KnowledgeNode)
            RETURN properties(a) AS source, properties(b) AS target,
                   type(r) AS rel_type, properties(r) AS props
            """
        )

        self.graph.clear()
        for record in records:
            labels = set(record.get("labels") or [])
            props = dict(record.get("props") or {})
            key = self._first_present(props, "uid", "node_id", "id", "code")
            if not key:
                continue
            if "Pillar" in labels:
                self.add_pillar(
                    str(key),
                    code=self._optional_str(props.get("code") or props.get("pillar_id")),
                    name=self._optional_str(props.get("name") or props.get("title")),
                    data=props,
                )
            else:
                self.add_knowledge_node(
                    str(key),
                    node_id=self._optional_str(props.get("node_id")),
                    title=self._optional_str(props.get("title") or props.get("label")),
                    axis_number=props.get("axis_number"),
                    data=props,
                )

        for record in rel_records:
            source_props = dict(record.get("source") or {})
            target_props = dict(record.get("target") or {})
            source = self._first_present(source_props, "uid", "node_id", "id", "code")
            target = self._first_present(target_props, "uid", "node_id", "id", "code")
            if source and target:
                self.add_relationship(
                    str(source),
                    str(target),
                    self._optional_str(record.get("rel_type")) or "RELATED_TO",
                    data=dict(record.get("props") or {}),
                )

        self.last_loaded_at = datetime.now(UTC)
        return self.stats()

    def load_from_database(self, db_session: Any) -> UskdGraphStats:
        """Load PillarLevel, KnowledgeGraphNode, and KnowledgeGraphEdge rows."""
        from sqlalchemy import inspect
        from models import KnowledgeGraphEdge, KnowledgeGraphNode, PillarLevel

        bind = db_session.get_bind() if hasattr(db_session, "get_bind") else getattr(db_session, "bind", None)
        if bind is None:
            logger.info("USKD SQL load skipped; no database bind available")
            return self.stats()
        inspector = inspect(bind)
        table_names = set(inspector.get_table_names())
        required_tables = {
            PillarLevel.__tablename__,
            KnowledgeGraphNode.__tablename__,
            KnowledgeGraphEdge.__tablename__,
        }
        if not required_tables.issubset(table_names):
            missing = sorted(required_tables - table_names)
            logger.info("USKD SQL load skipped; missing tables: %s", missing)
            return self.stats()

        return self.load_from_records(
            pillars=db_session.query(PillarLevel).all(),
            knowledge_nodes=db_session.query(KnowledgeGraphNode).all(),
            edges=db_session.query(KnowledgeGraphEdge).all(),
        )

    def add_pillar(
        self,
        uid: str,
        *,
        code: Optional[str] = None,
        name: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.graph.add_node(
            uid,
            kind="pillar",
            code=code,
            name=name,
            data=dict(data or {}),
        )

    def add_knowledge_node(
        self,
        uid: str,
        *,
        node_id: Optional[str] = None,
        title: Optional[str] = None,
        axis_number: Any = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.graph.add_node(
            uid,
            kind="knowledge_node",
            node_id=node_id,
            title=title,
            axis_number=axis_number,
            data=dict(data or {}),
        )

    def add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        *,
        weight: Any = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if source not in self.graph:
            self.graph.add_node(source, kind="external")
        if target not in self.graph:
            self.graph.add_node(target, kind="external")
        self.graph.add_edge(
            source,
            target,
            relationship_type=relationship_type,
            weight=self._coerce_weight(weight),
            data=dict(data or {}),
        )

    def upsert_authorized_knowledge_node(
        self,
        uid: str,
        *,
        node_id: Optional[str] = None,
        title: Optional[str] = None,
        axis_number: Any = None,
        pillar_uid: Optional[str] = None,
        relationship_type: str = "AUTHORIZED_KNOWLEDGE",
        data: Optional[Mapping[str, Any]] = None,
    ) -> UskdGraphStats:
        """Update the in-process graph after a release-gated knowledge commit."""
        self.add_knowledge_node(
            uid,
            node_id=node_id,
            title=title,
            axis_number=axis_number,
            data=data,
        )
        if pillar_uid:
            self.add_relationship(str(pillar_uid), uid, relationship_type)
        return self.stats()

    def coordinate_nodes(self, *, axis_number: Optional[int] = None, text: str = "", limit: int = 25) -> list[dict[str, Any]]:
        """Find candidate graph anchors for a coordinate/text pair."""
        matches: list[dict[str, Any]] = []
        needle = str(text or "").strip().lower()
        for uid, attrs in self.graph.nodes(data=True):
            if axis_number is not None and attrs.get("axis_number") not in (None, axis_number):
                continue
            if needle:
                data = attrs.get("data") if isinstance(attrs.get("data"), dict) else {}
                haystack = " ".join(
                    str(value or "")
                    for value in (
                        uid,
                        attrs.get("name"),
                        attrs.get("title"),
                        attrs.get("code"),
                        attrs.get("node_id"),
                        data.get("description"),
                        data.get("content"),
                    )
                ).lower()
                if needle not in haystack:
                    continue
            matches.append({"uid": uid, **attrs})
            if len(matches) >= limit:
                break
        return matches

    def neighborhood(self, uid: str, *, depth: int = 1) -> dict[str, Any]:
        """Return a bounded directed neighborhood around a node."""
        if uid not in self.graph:
            return {"center": uid, "nodes": [], "edges": []}

        depth = max(0, int(depth))
        visited = {uid}
        frontier = {uid}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                next_frontier.update(str(n) for n in self.graph.successors(node))
                next_frontier.update(str(n) for n in self.graph.predecessors(node))
            next_frontier -= visited
            visited.update(next_frontier)
            frontier = next_frontier

        subgraph = self.graph.subgraph(visited)
        return {
            "center": uid,
            "nodes": [
                {"uid": node, **attrs}
                for node, attrs in sorted(subgraph.nodes(data=True), key=lambda item: str(item[0]))
            ],
            "edges": [
                {"source": source, "target": target, **attrs}
                for source, target, attrs in subgraph.edges(data=True)
            ],
        }

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Simple metadata search for bootstrap/debug use."""
        needle = str(query or "").strip().lower()
        if not needle:
            return []

        matches: list[dict[str, Any]] = []
        for uid, attrs in self.graph.nodes(data=True):
            haystack = " ".join(
                str(value or "")
                for value in (
                    uid,
                    attrs.get("name"),
                    attrs.get("title"),
                    attrs.get("node_id"),
                    attrs.get("code"),
                    attrs.get("data", {}).get("description") if isinstance(attrs.get("data"), dict) else "",
                    attrs.get("data", {}).get("content") if isinstance(attrs.get("data"), dict) else "",
                )
            ).lower()
            if needle in haystack:
                matches.append({"uid": uid, **attrs})
                if len(matches) >= limit:
                    break
        return matches

    def stats(self) -> UskdGraphStats:
        kinds = nx.get_node_attributes(self.graph, "kind")
        return UskdGraphStats(
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
            pillar_count=sum(1 for kind in kinds.values() if kind == "pillar"),
            knowledge_node_count=sum(1 for kind in kinds.values() if kind == "knowledge_node"),
            last_loaded_at=self.last_loaded_at.isoformat() if self.last_loaded_at else None,
        )

    @staticmethod
    def _record_to_mapping(record: Any) -> dict[str, Any]:
        if record is None:
            return {}
        if isinstance(record, Mapping):
            return dict(record)
        if hasattr(record, "to_dict"):
            return dict(record.to_dict())
        return {
            key: value
            for key, value in vars(record).items()
            if not key.startswith("_")
        }

    @staticmethod
    def _first_present(data: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _optional_str(value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        return str(value)

    @staticmethod
    def _coerce_weight(value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


_uskd_memory_graph: Optional[UskdMemoryGraph] = None


def get_uskd_memory_graph() -> UskdMemoryGraph:
    """Return the USKD materialization owned by the active application."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            graph = current_app.extensions.get("dle_uskd_memory_graph")
            if graph is None:
                graph = UskdMemoryGraph()
                current_app.extensions["dle_uskd_memory_graph"] = graph
            return graph
    except ImportError:
        pass

    global _uskd_memory_graph
    if _uskd_memory_graph is None:
        _uskd_memory_graph = UskdMemoryGraph()
    return _uskd_memory_graph
