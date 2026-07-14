"""Unified persistent memory service for TruthCore and L10 Lane B."""

from __future__ import annotations

import atexit
import copy
from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any

import numpy as np

from backend.truth_engine.truth_core.historical_embeddings import text_to_embedding
from core.persona.quad.mathematical_framework import MemoryEdge, MemoryVertex, StructuredMemoryGraph

logger = logging.getLogger(__name__)


class UnifiedMemoryService:
    """Wrap StructuredMemoryGraph with local persistence and layer/persona namespacing."""

    DEFAULT_PATH = Path("databases/memory/memory_graph.json")
    SCHEMA_VERSION = 2

    def __init__(
        self,
        *,
        graph: StructuredMemoryGraph | None = None,
        storage_path: str | Path | None = None,
        auto_load: bool = True,
        strict: bool = False,
    ):
        self.graph = graph or StructuredMemoryGraph()
        self.storage_path = Path(
            storage_path
            or os.environ.get("DLE_MEMORY_GRAPH_PATH")
            or self.DEFAULT_PATH
        )
        self.last_recall_timestamp: str | None = None
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self.strict = bool(strict)
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
        payload = {
            "version": self.SCHEMA_VERSION,
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
        payload["integrity_sha256"] = self._payload_sha256(payload)
        return payload

    def load_graph(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict) or payload.get("version") != self.SCHEMA_VERSION:
            raise ValueError("unified_memory_schema_version_incompatible")
        expected_hash = str(payload.get("integrity_sha256") or "")
        if not expected_hash or expected_hash != self._payload_sha256(payload):
            raise ValueError("unified_memory_integrity_invalid")
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
            backup = self.storage_path.with_suffix(self.storage_path.suffix + ".bak")
            try:
                self.load_graph(json.loads(backup.read_text(encoding="utf-8")))
                self._atomic_write(self.export_graph(), preserve_backup=True)
                logger.warning("Structured memory graph recovered from verified backup")
            except Exception:
                if self.strict:
                    raise exc
                logger.warning("Structured memory graph load skipped: %s", exc)

    def save(self) -> None:
        try:
            self._atomic_write(self.export_graph(), preserve_backup=False)
        except Exception as exc:  # pylint: disable=broad-except
            if self.strict:
                raise
            logger.warning("Structured memory graph save skipped: %s", exc)

    def _atomic_write(self, payload: dict[str, Any], *, preserve_backup: bool) -> None:
        temporary = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        backup = self.storage_path.with_suffix(self.storage_path.suffix + ".bak")
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            if self.storage_path.is_file() and not preserve_backup:
                try:
                    current = json.loads(self.storage_path.read_text(encoding="utf-8"))
                    if (
                        isinstance(current, dict)
                        and current.get("version") == self.SCHEMA_VERSION
                        and current.get("integrity_sha256") == self._payload_sha256(current)
                    ):
                        shutil.copy2(self.storage_path, backup)
                except (OSError, ValueError):
                    pass
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.storage_path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _payload_sha256(payload: dict[str, Any]) -> str:
        canonical = dict(payload)
        canonical.pop("integrity_sha256", None)
        return hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode(
                "utf-8"
            )
        ).hexdigest()

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
            validation_state = str(
                vertex.metadata.get("validation_state") or "working"
            )
            same_working_session = bool(
                context.get("session_id")
                and vertex.metadata.get("session_id") == context.get("session_id")
            )
            if validation_state != "validated" and not same_working_session:
                continue
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
        trusted: bool = False,
        source_run_id: str | None = None,
        policy_result: str | None = None,
        retention_class: str | None = None,
    ) -> MemoryVertex:
        """Persist or strengthen a memory vertex through StructuredMemoryGraph MC(M,I,t)."""
        if trusted and (not source_run_id or policy_result != "release_authorized"):
            raise ValueError("trusted_memory_requires_release_authority")
        metadata = {
            **(metadata or {}),
            "layer": layer,
            "persona": persona,
            "source": (metadata or {}).get("source", "unified_memory_service"),
            "source_run_id": source_run_id,
            "policy_result": policy_result or "working_only",
            "validation_state": "validated" if trusted else "working",
            "retention_class": retention_class or (
                "validated_reasoning_memory" if trusted else "session_working_memory"
            ),
        }
        existing = self._find_existing(
            content,
            layer=layer,
            persona=persona,
            validation_state=metadata["validation_state"],
        )
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
            trusted=False,
            source_run_id=str((context or {}).get("run_id") or "") or None,
            policy_result="working_only",
            retention_class="session_working_memory",
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
            trusted=True,
            source_run_id=simulation_id,
            policy_result="release_authorized",
            retention_class="validated_reasoning_memory",
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

    def review(self, *, include_working: bool = False) -> list[dict[str, Any]]:
        """Return bounded memory records for owner review without embeddings."""
        records = []
        for vertex in sorted(
            self.graph.vertices.values(), key=lambda item: item.timestamp, reverse=True
        ):
            state = str(vertex.metadata.get("validation_state") or "working")
            if state != "validated" and not include_working:
                continue
            records.append(
                {
                    "vertex_id": vertex.vertex_id,
                    "content": vertex.content,
                    "validation_state": state,
                    "source_run_id": vertex.metadata.get("source_run_id"),
                    "policy_result": vertex.metadata.get("policy_result"),
                    "retention_class": vertex.metadata.get("retention_class"),
                    "session_id": vertex.metadata.get("session_id"),
                    "created_at": vertex.timestamp.isoformat(),
                    "last_accessed": vertex.last_accessed.isoformat(),
                }
            )
        return records

    def delete(self, vertex_id: str) -> bool:
        """Delete one reviewed memory vertex and every connected edge."""
        if not self._delete_without_save(vertex_id):
            return False
        self.save()
        return True

    def delete_by_sources(
        self,
        *,
        source_ids: set[str] | None = None,
        ingestion_id: str | None = None,
        document_uids: set[str] | None = None,
    ) -> int:
        """Delete memories whose recorded provenance references removed sources."""
        expected_sources = {str(value) for value in (source_ids or set()) if value}
        expected_documents = {str(value) for value in (document_uids or set()) if value}
        matched: list[str] = []
        for vertex in self.graph.vertices.values():
            metadata = vertex.metadata or {}
            recorded_sources = {
                str(value)
                for key in ("source_ids", "evidence_source_ids")
                for value in (
                    metadata.get(key) if isinstance(metadata.get(key), list) else []
                )
            }
            recorded_document = str(metadata.get("document_uid") or "")
            if (
                expected_sources.intersection(recorded_sources)
                or (ingestion_id and str(metadata.get("ingestion_id") or "") == ingestion_id)
                or (recorded_document and recorded_document in expected_documents)
            ):
                matched.append(vertex.vertex_id)
        for vertex_id in matched:
            self._delete_without_save(vertex_id)
        if matched:
            self.save()
        return len(matched)

    def _delete_without_save(self, vertex_id: str) -> bool:
        normalized = str(vertex_id or "").strip()
        if normalized not in self.graph.vertices:
            return False
        self.graph.vertices.pop(normalized, None)
        self.graph.adjacency.pop(normalized, None)
        for targets in self.graph.adjacency.values():
            targets.discard(normalized)
        edges = self.graph.edges
        if isinstance(edges, dict):
            self.graph.edges = {
                key: edge
                for key, edge in edges.items()
                if edge.source_id != normalized and edge.target_id != normalized
            }
        else:
            self.graph.edges = [
                edge
                for edge in edges
                if edge.source_id != normalized and edge.target_id != normalized
            ]
        return True

    def compact(self, *, max_working_vertices: int = 500) -> dict[str, int]:
        """Bound session-working state without deleting validated memories."""
        limit = max(0, min(10_000, int(max_working_vertices)))
        working = sorted(
            (
                vertex
                for vertex in self.graph.vertices.values()
                if vertex.metadata.get("validation_state") != "validated"
            ),
            key=lambda item: item.last_accessed,
            reverse=True,
        )
        removed = 0
        for vertex in working[limit:]:
            removed += self.delete(vertex.vertex_id)
        return {"working_before": len(working), "removed": removed, "working_after": len(working) - removed}

    def recover_from_backup(self) -> dict[str, Any]:
        """Restore only from a schema-compatible, integrity-verified backup."""
        backup = self.storage_path.with_suffix(self.storage_path.suffix + ".bak")
        payload = json.loads(backup.read_text(encoding="utf-8"))
        self.load_graph(payload)
        self._atomic_write(self.export_graph(), preserve_backup=True)
        return self.stats()

    def _find_existing(
        self,
        content: str,
        *,
        layer: str,
        persona: str,
        validation_state: str,
    ) -> MemoryVertex | None:
        for vertex in self.graph.vertices.values():
            if (
                vertex.content == content
                and vertex.metadata.get("layer") == layer
                and vertex.metadata.get("persona") == persona
                and vertex.metadata.get("validation_state") == validation_state
            ):
                return vertex
        return None


_unified_memory_service: UnifiedMemoryService | None = None


def get_unified_memory_service() -> UnifiedMemoryService:
    """Return the memory service owned by the active application."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            service = current_app.extensions.get("dle_unified_memory_service")
            if service is None:
                runtime = current_app.extensions.get("dle_runtime")
                storage_path = (
                    runtime.runtime_root / "databases" / "memory" / "memory_graph.json"
                    if runtime is not None
                    else None
                )
                service = UnifiedMemoryService(storage_path=storage_path)
                current_app.extensions["dle_unified_memory_service"] = service
            return service
    except ImportError:
        pass

    global _unified_memory_service
    if _unified_memory_service is None:
        _unified_memory_service = UnifiedMemoryService()
        atexit.register(_unified_memory_service.save)
    return _unified_memory_service
