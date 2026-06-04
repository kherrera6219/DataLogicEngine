"""Dynamic weighting and knowledge-space mapping for Quad Persona math."""

import json
import math
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import numpy as np

from core.persona.quad.mathematical_framework.memory_graph import KnowledgePoint


class DynamicWeightFunctions:
    """Implements dynamic weight functions for persona weighting."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.learning_rate = self.config.get("learning_rate", 0.01)
        self.decay_rate = self.config.get("decay_rate", 0.1)
        self.base_weights = {
            "knowledge": 1.0,
            "sector": 1.0,
            "regulatory": 1.0,
            "compliance": 1.0,
        }
        self.weight_history = []

    def alpha(self, t: float, component_idx: int = 0) -> float:
        """Time-dependent weight for Knowledge Expert."""
        t_optimal = self.config.get("knowledge_optimal_time", 0.5)
        decay = self.config.get("knowledge_decay", 0.5)
        base = self.base_weights["knowledge"]
        return base * math.exp(-decay * abs(t - t_optimal))

    def beta(self, context: Dict[str, Any], component_idx: int = 0) -> float:
        """Context-dependent weight for Sector Expert."""
        sector_relevance = context.get("sector_relevance", 1.0)
        industry_match = context.get("industry_match", 1.0)
        base = self.base_weights["sector"]
        return base * sector_relevance * industry_match

    def gamma(self, context: Dict[str, Any], t: float, component_idx: int = 0) -> float:
        """Combined context and time weight for Regulatory Expert."""
        regulatory_urgency = context.get("regulatory_urgency", 1.0)
        compliance_deadline = context.get("compliance_deadline", None)
        base = self.base_weights["regulatory"]

        temporal_factor = 1.0
        if compliance_deadline:
            days_until = (compliance_deadline - datetime.now(UTC)).days
            if days_until <= 30:
                temporal_factor = 2.0 - (days_until / 30)
            elif days_until <= 90:
                temporal_factor = 1.5 - (days_until - 30) / 120

        return base * regulatory_urgency * temporal_factor

    def delta(self, context: Dict[str, Any], t: float, component_idx: int = 0) -> float:
        """Combined context and time weight for Compliance Expert."""
        compliance_criticality = context.get("compliance_criticality", 1.0)
        audit_proximity = context.get("audit_proximity", 1.0)
        base = self.base_weights["compliance"]
        return base * compliance_criticality * audit_proximity

    def compute_all_weights(self, context: Dict[str, Any], t: float = None) -> Dict[str, float]:
        """Compute all persona weights given context and time."""
        if t is None:
            t = 0.5

        weights = {
            "knowledge": self.alpha(t),
            "sector": self.beta(context),
            "regulatory": self.gamma(context, t),
            "compliance": self.delta(context, t),
        }

        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        self.weight_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "weights": json.loads(json.dumps(weights.copy(), sort_keys=True, default=float)),
            "context_keys": sorted(str(key) for key in context.keys()),
        })

        return weights

    def get_serializable_weight_history(self) -> List[Dict[str, Any]]:
        """Return weight history guaranteed to survive JSON/SQLite storage."""
        return json.loads(json.dumps(self.weight_history, sort_keys=True, default=str))

    def update_weights(self, gradient: Dict[str, float]):
        """Update base weights using gradient descent."""
        for persona_type, grad in gradient.items():
            if persona_type in self.base_weights:
                self.base_weights[persona_type] += self.learning_rate * grad
                self.base_weights[persona_type] = max(0.1, min(2.0, self.base_weights[persona_type]))


class KnowledgeSpaceMapper:
    """Maps queries to relevant points in the knowledge manifold."""

    def __init__(self, relevance_threshold: float = 0.3):
        self.theta = relevance_threshold
        self.knowledge_points: List[Tuple[KnowledgePoint, Dict[str, Any]]] = []
        self.pillar_embeddings: Dict[str, np.ndarray] = {}

    def add_knowledge_point(self, point: KnowledgePoint, metadata: Dict[str, Any] = None):
        """Add a knowledge point to the space."""
        self.knowledge_points.append((point, metadata or {}))

    def similarity(
        self,
        query_vec: np.ndarray,
        point_vec: np.ndarray,
        context: Dict[str, Any] = None,
        t: float = None,
    ) -> float:
        """Compute similarity between query and knowledge point."""
        norm_q = np.linalg.norm(query_vec)
        norm_p = np.linalg.norm(point_vec)

        if norm_q == 0 or norm_p == 0:
            return 0.0

        cosine_sim = np.dot(query_vec, point_vec) / (norm_q * norm_p)

        context_boost = 1.0
        if context:
            if context.get("pillar_match"):
                context_boost *= 1.5
            if context.get("sector_match"):
                context_boost *= 1.3

        temporal_decay = 1.0
        if t is not None:
            temporal_decay = math.exp(-0.1 * abs(t))

        return cosine_sim * context_boost * temporal_decay

    def map_query(
        self,
        query_vec: np.ndarray,
        context: Dict[str, Any] = None,
        t: float = None,
    ) -> List[Tuple[KnowledgePoint, float, Dict[str, Any]]]:
        """Dynamic knowledge mapping function M(q,c,t)."""
        context = context or {}
        results = []

        for point, metadata in self.knowledge_points:
            point_vec = point.to_vector()
            score = self.similarity(query_vec, point_vec, context, t)

            if score > self.theta:
                results.append((point, score, metadata))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def pillar_selection(
        self,
        query_vec: np.ndarray,
        context: Dict[str, Any] = None,
        dimension_weights: np.ndarray = None,
    ) -> Tuple[int, float]:
        """Pillar Selection Function PS(q, c)."""
        if dimension_weights is None:
            dimension_weights = np.ones(13) / 13

        best_pillar = None
        best_score = -float("inf")

        pillar_groups = {}
        for point, metadata in self.knowledge_points:
            pillar_id = int(point.pillar)
            if pillar_id not in pillar_groups:
                pillar_groups[pillar_id] = []
            pillar_groups[pillar_id].append(point)

        for pillar_id, points in pillar_groups.items():
            total_score = 0.0
            for point in points:
                point_vec = point.to_vector()
                for i, (w, q, p) in enumerate(zip(dimension_weights, query_vec, point_vec)):
                    total_score += w * (1 - abs(q - p))

            avg_score = total_score / len(points) if points else 0
            if avg_score > best_score:
                best_score = avg_score
                best_pillar = pillar_id

        return best_pillar, best_score

    def cross_dimensional_mapping(
        self,
        p1: KnowledgePoint,
        p2: KnowledgePoint,
        omega_weights: np.ndarray = None,
    ) -> float:
        """Cross-dimensional mapping CDM(p1, p2)."""
        if omega_weights is None:
            omega_weights = np.ones(13)

        v1 = p1.to_vector()
        v2 = p2.to_vector()

        weighted_sim = 0.0
        for i, (w, a, b) in enumerate(zip(omega_weights, v1, v2)):
            dim_sim = 1 - abs(a - b) / (max(abs(a), abs(b), 1))
            weighted_sim += w * dim_sim

        norm_factor = np.sqrt(np.sum(omega_weights ** 2))
        if norm_factor == 0:
            return 0.0

        return weighted_sim / norm_factor
