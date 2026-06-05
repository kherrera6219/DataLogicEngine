"""Structured memory graph primitives for the Quad Persona mathematical framework."""

import math
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


@dataclass
class KnowledgePoint:
    """A point in the 17-dimensional knowledge manifold."""

    # Group I - Knowledge Organization
    pillar: float = 0.0
    sector: float = 0.0
    honeycomb: float = 0.0
    branch: float = 0.0
    node: float = 0.0
    octopus: float = 0.0
    spiderweb: float = 0.0

    # Group III - Context
    location: float = 0.0
    temporal: float = 0.0

    # Group IV - Governance (Meta-axes)
    provenance: float = 0.0
    object_type: float = 0.0
    validation_state: float = 0.0
    security: float = 0.0

    # Derived values
    confidence: float = 0.0
    methodology: float = 0.0
    knowledge_level: float = 0.0

    def to_vector(self) -> np.ndarray:
        """Convert to numpy array (16 dimensions)."""
        return np.array([
            self.pillar,
            self.sector,
            self.honeycomb,
            self.branch,
            self.node,
            self.octopus,
            self.spiderweb,
            self.location,
            self.temporal,
            self.provenance,
            self.object_type,
            self.validation_state,
            self.security,
            self.confidence,
            self.methodology,
            self.knowledge_level,
        ])

    @classmethod
    def from_vector(cls, vec: np.ndarray) -> "KnowledgePoint":
        """Create from numpy array."""
        return cls(*vec[:16]) if len(vec) >= 16 else cls(*vec)


@dataclass
class MemoryVertex:
    """A vertex in the memory graph G_M."""

    vertex_id: str
    content: str
    embedding: Optional[np.ndarray] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    importance: float = 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEdge:
    """An edge in the memory graph G_M."""

    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StructuredMemoryGraph:
    """Structured Memory Graph G_M = (V_M, E_M, A_M)."""

    def __init__(self, memory_threshold: float = 0.3):
        self.theta_m = memory_threshold
        self.vertices: Dict[str, MemoryVertex] = {}
        self.edges: List[MemoryEdge] = {}
        self.adjacency: Dict[str, Set[str]] = {}

    def add_vertex(self, vertex: MemoryVertex):
        """Add a memory vertex."""
        self.vertices[vertex.vertex_id] = vertex
        if vertex.vertex_id not in self.adjacency:
            self.adjacency[vertex.vertex_id] = set()

    def add_edge(self, edge: MemoryEdge):
        """Add a memory edge."""
        edge_key = f"{edge.source_id}->{edge.target_id}"
        self.edges[edge_key] = edge
        if edge.source_id not in self.adjacency:
            self.adjacency[edge.source_id] = set()
        self.adjacency[edge.source_id].add(edge.target_id)

    def memory_access(
        self,
        query_vec: np.ndarray,
        context: Dict[str, Any] = None,
        t: float = None,
    ) -> List[MemoryVertex]:
        """Memory Access Function MA(q, c, t)."""
        results = []
        context = context or {}

        for vertex_id, vertex in self.vertices.items():
            if vertex.embedding is None:
                continue

            norm_q = np.linalg.norm(query_vec)
            norm_m = np.linalg.norm(vertex.embedding)

            if norm_q == 0 or norm_m == 0:
                continue

            sim = np.dot(query_vec, vertex.embedding) / (norm_q * norm_m)

            if sim > self.theta_m:
                vertex.access_count += 1
                vertex.last_accessed = datetime.now(UTC)
                results.append(vertex)

        return results

    def structured_recall(
        self,
        query_vec: np.ndarray,
        context: Dict[str, Any] = None,
        t: float = None,
    ) -> Tuple[np.ndarray, List[MemoryVertex]]:
        """Structured Recall Algorithm SR(q, c, t)."""
        accessed_memories = self.memory_access(query_vec, context, t)

        if not accessed_memories:
            return np.zeros_like(query_vec), []

        weighted_sum = np.zeros_like(accessed_memories[0].embedding)

        for memory in accessed_memories:
            relevance = self._relevance_function(memory, query_vec, context)
            temporal = self._temporal_importance(memory, t)
            importance = memory.importance

            weight = relevance * temporal * importance
            weighted_sum += weight * memory.embedding

        return weighted_sum, accessed_memories

    def _relevance_function(
        self,
        memory: MemoryVertex,
        query_vec: np.ndarray,
        context: Dict[str, Any],
    ) -> float:
        """R(m, q, c): Relevance function."""
        if memory.embedding is None:
            return 0.0

        norm_q = np.linalg.norm(query_vec)
        norm_m = np.linalg.norm(memory.embedding)

        if norm_q == 0 or norm_m == 0:
            return 0.0

        return np.dot(query_vec, memory.embedding) / (norm_q * norm_m)

    def _temporal_importance(self, memory: MemoryVertex, t: float = None) -> float:
        """T(m, t): Temporal importance function with decay."""
        if t is None:
            age_days = (datetime.now(UTC) - memory.timestamp).days
        else:
            age_days = t

        decay_rate = 0.01
        return math.exp(-decay_rate * age_days)

    def memory_consolidation(
        self,
        new_info: Dict[str, Any],
        existing_memory: Optional[MemoryVertex] = None,
    ) -> MemoryVertex:
        """Memory Consolidation Function MC(M, I, t)."""
        if existing_memory and existing_memory.vertex_id in self.vertices:
            existing_memory.content = new_info.get("content", existing_memory.content)
            if "embedding" in new_info:
                if existing_memory.embedding is not None:
                    existing_memory.embedding = 0.5 * existing_memory.embedding + 0.5 * new_info["embedding"]
                else:
                    existing_memory.embedding = new_info["embedding"]
            existing_memory.importance = min(2.0, existing_memory.importance + 0.1)
            return existing_memory

        new_vertex = MemoryVertex(
            vertex_id=str(uuid.uuid4()),
            content=new_info.get("content", ""),
            embedding=new_info.get("embedding"),
            importance=new_info.get("importance", 1.0),
            metadata=new_info.get("metadata", {}),
        )
        self.add_vertex(new_vertex)
        return new_vertex
