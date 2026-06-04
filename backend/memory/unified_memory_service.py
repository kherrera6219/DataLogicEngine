"""Unified persistent memory service for TruthCore and L10 Lane B."""

from __future__ import annotations

import atexit
import copy
from dataclasses import asdict
from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

from backend.truth_engine.truth_core.historical_embeddings import text_to_embedding
from core.persona.quad.mathematical_framework import MemoryEdge, MemoryVertex, StructuredMemoryGraph

logger = logging.getLogger(__name__)


class UnifiedMemoryService:
    """Wrap StructuredMemoryGraph with local persistence and layer/persona namespacing."""

    DEFAULT_PATH = Path("databases/memory/memory_graph.json")

    def __init__(
        self,
        *,
        graph: StructuredMemoryGraph | None = None,
        storage_path: str | Path | None = None,
        auto_load: bool = True,
    ):
        self.graph = graph or StructuredMemoryGraph()
        self.storage_path = Path(
            storage_path
            or os.environ.get("DLE_MEMORY_GRAPH_PATH")
            or self.DEFAULT_PATH
        )
        self.last_recall_timestamp: str | None = None
        self._checkpoints: dict[str, dict[str, Any]] = {}
        if auto_load:
            self.load()

    @staticmethod
    def _embedding(text: str) -> np.ndarray:
        return np.array(text_to_embedding(text or ""), dtype=float)

    @staticmethod
    def _vertex_to_dict(vertex: MemoryVertex) -> dict[str, Any]:
        payload = asdict(vertex)
        payload["embedding"] = vertex.embedding.tolist() if vertex.embedding is not None else None
        payload["timestamp"] = vertex.timestamp.isoformat()
        payload["last_accessed"] = vertex.last_accessed.isoformat()
        return payload

    @staticmethod
    def _edge_to_dict(edge: MemoryEdge) -> dict[str, Any]:
        return asdict(edge)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if value:
            parsed = datetime.fromisoformat(str(value))
        else:
            parsed = datetime.now(UTC)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _vertex_from_dict(payload: dict[str, Any]) -> MemoryVertex:
        embedding = payload.get("embedding")
        return MemoryVertex(
            vertex_id=str(payload.get("vertex_id") or ""),
            content=str(payload.get("content") or ""),
            embedding=np.array(embedding, dtype=float) if isinstance(embedding, list) else None,
            timestamp=UnifiedMemoryService._parse_datetime(payload.get("timestamp")),
            importance=float(payload.get("importance", 1.0)),
            access_count=int(payload.get("access_count", 0)),
            last_accessed=UnifiedMemoryService._parse_datetime(payload.get("last_accessed")),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )

    @staticmethod
    def _edge_from_dict(payload: dict[str, Any]) -> MemoryEdge:
        return MemoryEdge(
            source_id=str(payload.get("source_id") or ""),
            target_id=str(payload.get("target_id") or ""),
            edge_type=str(payload.get("edge_type") or "related"),
            weight=float(payload.get("weight", 1.0)),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )

    def export_graph(self) -> dict[str, Any]:
        edges = self.graph.edges.values() if isinstance(self.graph.edges, dict) else self.graph.edges
        return {
            "version": 1,
            "saved_at": datetime.now(UTC).isoformat(),
            "last_recall_timestamp": self.last_recall_timestamp,
            "vertices": [
                self._vertex_to_dict(vertex)
                for vertex in self.graph.vertices.values()
            ],
            "edges": [
                self._edge_to_dict(edge)
                for edge in edges
            ],
        }

    def load_graph(self, payload: dict[str, Any]) -> None:
        self.graph.vertices.clear()
        self.graph.adjacency.clear()
        self.graph.edges = {}
        for vertex_payload in payload.get("vertices", []):
            if not isinstance(vertex_payload, dict):
                continue
            vertex = self._vertex_from_dict(vertex_payload)
            if vertex.vertex_id:
                self.graph.add_vertex(vertex)
        for edge_payload in payload.get("edges", []):
            if not isinstance(edge_payload, dict):
                continue
            edge = self._edge_from_dict(edge_payload)
            if edge.source_id and edge.target_id:
                self.graph.add_edge(edge)
        self.last_recall_timestamp = payload.get("last_recall_timestamp")

    def load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            self.load_graph(json.loads(self.storage_path.read_text(encoding="utf-8")))
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Structured memory graph load skipped: %s", exc)

    def save(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(self.export_graph(), sort_keys=True, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Structured memory graph save skipped: %s", exc)

    def recall(
        self,
        query: str,
        *,
        layer: str | None = None,
        persona: str | None = None,
        context: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[MemoryVertex]:
        """Return ranked memories for the query, optionally scoped by layer/persona."""
        query_vec = self._embedding(query)
        context = context or {}
        ranked: list[tuple[float, MemoryVertex]] = []
        for vertex in self.graph.vertices.values():
            if layer and vertex.metadata.get("layer") not in {layer, "global", None}:
                continue
            if persona and vertex.metadata.get("persona") not in {persona, "global", None}:
                continue
            if vertex.embedding is None:
                continue
            relevance = self.graph._relevance_function(vertex, query_vec, context)  # pylint: disable=protected-access
            if relevance < self.graph.theta_m:
                continue
            temporal = self.graph._temporal_importance(vertex)  # pylint: disable=protected-access
            score = relevance * temporal * float(vertex.importance)
            ranked.append((score, vertex))

        ranked.sort(key=lambda item: item[0], reverse=True)
        memories = [vertex for _, vertex in ranked[:limit]]
        now = datetime.now(UTC)
        self.last_recall_timestamp = now.isoformat()
        for vertex in memories:
            vertex.access_count += 1
            vertex.last_accessed = now
            vertex.importance = min(2.0, float(vertex.importance) + 0.01)
        return memories

    def consolidate(
        self,
        content: str,
        *,
        layer: str = "global",
        persona: str = "global",
        metadata: dict[str, Any] | None = None,
        importance: float = 1.0,
    ) -> MemoryVertex:
        """Persist or strengthen a memory vertex through StructuredMemoryGraph MC(M,I,t)."""
        metadata = {
            **(metadata or {}),
            "layer": layer,
            "persona": persona,
            "source": (metadata or {}).get("source", "unified_memory_service"),
        }
        existing = self._find_existing(content, layer=layer, persona=persona)
        vertex = self.graph.memory_consolidation(
            {
                "content": content,
                "embedding": self._embedding(content),
                "importance": importance,
                "metadata": metadata,
            },
            existing_memory=existing,
        )
        if vertex.timestamp.tzinfo is None:
            vertex.timestamp = vertex.timestamp.replace(tzinfo=UTC)
        if vertex.last_accessed.tzinfo is None:
            vertex.last_accessed = vertex.last_accessed.replace(tzinfo=UTC)
        vertex.metadata.update(metadata)
        self.save()
        return vertex

    def record_layer_result(
        self,
        *,
        query: str,
        layer: str,
        step: str,
        result: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> MemoryVertex:
        output = result.get("output")
        content = json.dumps(output, sort_keys=True, default=str) if isinstance(output, dict) else str(output)
        summary = f"{step}: {content[:1200]}"
        persona = str((context or {}).get("active_persona") or "global")
        return self.consolidate(
            summary,
            layer=layer,
            persona=persona,
            metadata={
                "query": query,
                "step": step,
                "session_id": (context or {}).get("session_id"),
                "confidence": result.get("confidence"),
            },
        )

    def record_release_commit(
        self,
        *,
        content: str,
        simulation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryVertex:
        return self.consolidate(
            content,
            layer="L10",
            persona="global",
            metadata={
                **(metadata or {}),
                "simulation_id": simulation_id,
                "source": "l10_lane_b",
            },
            importance=1.2,
        )

    def checkpoint(self, checkpoint_id: str) -> str:
        self._checkpoints[checkpoint_id] = copy.deepcopy(self.export_graph())
        return checkpoint_id

    def restore(self, checkpoint_id: str) -> bool:
        payload = self._checkpoints.get(checkpoint_id)
        if not payload:
            return False
        self.load_graph(copy.deepcopy(payload))
        self.save()
        return True

    def stats(self) -> dict[str, Any]:
        edge_count = len(self.graph.edges) if isinstance(self.graph.edges, dict) else len(list(self.graph.edges))
        return {
            "status": "ok",
            "memory_vertices": len(self.graph.vertices),
            "memory_edges": edge_count,
            "last_recall_timestamp": self.last_recall_timestamp,
            "storage_path": str(self.storage_path),
        }

    def _find_existing(self, content: str, *, layer: str, persona: str) -> MemoryVertex | None:
        for vertex in self.graph.vertices.values():
            if (
                vertex.content == content
                and vertex.metadata.get("layer") == layer
                and vertex.metadata.get("persona") == persona
            ):
                return vertex
        return None


_unified_memory_service: UnifiedMemoryService | None = None


def get_unified_memory_service() -> UnifiedMemoryService:
    """Return the process-wide local memory service."""
    global _unified_memory_service
    if _unified_memory_service is None:
        _unified_memory_service = UnifiedMemoryService()
        atexit.register(_unified_memory_service.save)
    return _unified_memory_service
