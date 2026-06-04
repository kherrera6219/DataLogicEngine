"""
Query Analysis System (QAS)

Enterprise-grade query analysis and tier selection system.
Determines how much of the UKG system runs based on query complexity,
risk, regulatory intensity, and novelty.

Tier 1: Bypass (trivial queries, definitions)
Tier 2: Light reasoning (explanations)
Tier 3: Standard advisory (business decisions)
Tier 4: Regulated execution (compliance, legal)
Tier 5: Mission-critical (safety, zero-trust)
"""

import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ExecutionTier(Enum):
    """UKG execution tiers (1-5)."""
    TIER_1_BYPASS = 1
    TIER_2_LIGHT = 2
    TIER_3_STANDARD = 3
    TIER_4_REGULATED = 4
    TIER_5_CRITICAL = 5
    
    @property
    def name_short(self) -> str:
        return ["bypass", "light", "standard", "regulated", "critical"][self.value - 1]
    
    @property
    def confidence_threshold(self) -> float:
        """Minimum confidence required for tier."""
        return [0.85, 0.90, 0.95, 0.98, 0.995][self.value - 1]
    
    @property
    def max_recursions(self) -> int:
        """Maximum refinement cycles for tier."""
        return [0, 1, 1, 2, 3][self.value - 1]


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ComplexityProfile:
    """
    Multi-dimensional query complexity profile.
    All scores normalized 0-100.
    """
    semantic_complexity: float = 0.0     # Ambiguity, depth, multi-part
    domain_breadth: float = 0.0          # Number of pillars/sectors activated
    risk_level: float = 0.0              # Axis 14 - safety/impact
    regulatory_intensity: float = 0.0   # Axes 6-7 triggered
    novelty_score: float = 0.0           # Axis 17 - memory delta
    
    def max_score(self) -> float:
        """Return maximum dimension score."""
        return max(
            self.semantic_complexity,
            self.domain_breadth,
            self.risk_level,
            self.regulatory_intensity,
            self.novelty_score
        )
    
    def weighted_score(self) -> float:
        """Weighted aggregate score."""
        return (
            self.semantic_complexity * 0.15 +
            self.domain_breadth * 0.15 +
            self.risk_level * 0.30 +
            self.regulatory_intensity * 0.30 +
            self.novelty_score * 0.10
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "semantic_complexity": self.semantic_complexity,
            "domain_breadth": self.domain_breadth,
            "risk_level": self.risk_level,
            "regulatory_intensity": self.regulatory_intensity,
            "novelty_score": self.novelty_score,
            "max_score": self.max_score(),
            "weighted_score": self.weighted_score()
        }


@dataclass
class TierDecision:
    """
    Complete tier selection decision with routing plan.
    """
    query_id: str = ""
    tier: ExecutionTier = ExecutionTier.TIER_3_STANDARD
    complexity_profile: ComplexityProfile = field(default_factory=ComplexityProfile)
    
    # Layer routing
    layers_to_run: List[int] = field(default_factory=list)
    personas_required: List[str] = field(default_factory=list)
    
    # Refinement
    run_refinement: bool = True
    max_refinement_cycles: int = 1
    
    # Thresholds
    confidence_threshold: float = 0.95
    
    # Reasoning
    decision_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = ""
    
    def __post_init__(self):
        if not self.query_id:
            import uuid
            self.query_id = f"qas_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.layers_to_run:
            self._set_default_layers()
    
    def _set_default_layers(self):
        """Set layers based on tier."""
        tier_layers = {
            ExecutionTier.TIER_1_BYPASS: [1, 2, 10],
            ExecutionTier.TIER_2_LIGHT: [1, 2, 5, 10],
            ExecutionTier.TIER_3_STANDARD: [1, 2, 3, 4, 5, 6, 8, 9, 10],
            ExecutionTier.TIER_4_REGULATED: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            ExecutionTier.TIER_5_CRITICAL: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
        self.layers_to_run = tier_layers.get(self.tier, [1, 2, 10])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "tier": self.tier.value,
            "tier_name": self.tier.name_short,
            "complexity_profile": self.complexity_profile.to_dict(),
            "layers_to_run": self.layers_to_run,
            "personas_required": self.personas_required,
            "run_refinement": self.run_refinement,
            "max_refinement_cycles": self.max_refinement_cycles,
            "confidence_threshold": self.confidence_threshold,
            "decision_reasons": self.decision_reasons,
            "created_at": self.created_at
        }


# =============================================================================
# Query Analysis System
# =============================================================================

class QueryAnalysisSystem:
    """
    Query Analysis System (QAS)
    
    Determines execution tier (1-5) based on multi-dimensional
    complexity analysis. Controls how much of UKG runs.
    """
    
    # Tier thresholds (max_score -> tier)
    TIER_THRESHOLDS = {
        20: ExecutionTier.TIER_1_BYPASS,
        40: ExecutionTier.TIER_2_LIGHT,
        60: ExecutionTier.TIER_3_STANDARD,
        80: ExecutionTier.TIER_4_REGULATED,
        100: ExecutionTier.TIER_5_CRITICAL
    }
    
    # Domain keywords for classification
    HIGH_RISK_DOMAINS = {
        "defense", "military", "weapons", "classified", "security",
        "healthcare", "medical", "patient", "clinical", "drug",
        "financial", "banking", "trading", "investment",
        "nuclear", "aviation", "critical infrastructure"
    }
    
    REGULATED_KEYWORDS = {
        "hipaa", "gdpr", "ccpa", "sox", "pci", "itar", "far", "dfars",
        "fda", "sec", "finra", "nerc", "ferc", "compliance", "audit",
        "regulatory", "certification", "authorization", "license"
    }
    
    SAFETY_KEYWORDS = {
        "safety", "hazard", "catastrophic", "life-threatening", "critical",
        "emergency", "fatal", "irreversible", "dangerous"
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize QAS."""
        self.config = config or {}
        
        # Override thresholds from config
        if "tier_thresholds" in self.config:
            for score, tier_val in self.config["tier_thresholds"].items():
                self.TIER_THRESHOLDS[int(score)] = ExecutionTier(tier_val)
        
        # Memory for novelty detection
        self._query_hashes: Set[str] = set()
        
        # Metrics
        self._total_queries = 0
        self._tier_distribution = {t: 0 for t in ExecutionTier}
        
        logger.info("QueryAnalysisSystem initialized")
    
    def analyze(
        self,
        query: str,
        context: Dict[str, Any] = None,
        axis_vector: Dict[int, Any] = None
    ) -> TierDecision:
        """
        Analyze query and determine execution tier.
        
        Args:
            query: Raw query text
            context: Additional context (domain, user role, etc.)
            axis_vector: Active axis mappings
            
        Returns:
            TierDecision with tier, layers, and routing plan
        """
        context = context or {}
        axis_vector = axis_vector or {}
        self._total_queries += 1
        
        logger.info(f"Analyzing query: {query[:50]}...")
        
        # Step 1: Compute complexity profile
        profile = self._compute_complexity(query, context, axis_vector)
        
        # Step 2: Select tier based on profile
        tier = self._select_tier(profile, context)
        
        # Step 3: Build tier decision
        decision = TierDecision(
            tier=tier,
            complexity_profile=profile,
            confidence_threshold=tier.confidence_threshold,
            max_refinement_cycles=tier.max_recursions,
            run_refinement=tier.value >= 2
        )
        
        # Step 4: Set personas based on tier
        decision.personas_required = self._select_personas(tier, profile)
        
        # Step 5: Add decision reasons
        decision.decision_reasons = self._generate_reasons(profile, tier)
        
        # Track metrics
        self._tier_distribution[tier] += 1
        
        logger.info(f"Tier decision: {tier.name_short} (score={profile.max_score():.1f})")
        
        return decision
    
    def _compute_complexity(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any]
    ) -> ComplexityProfile:
        """Compute multi-dimensional complexity profile."""
        profile = ComplexityProfile()
        query_lower = query.lower()
        
        # 1. Semantic complexity
        words = query.split()
        profile.semantic_complexity = min(100, len(words) * 1.5)
        
        # Multi-part queries
        if any(w in query_lower for w in ["and", "also", "plus", "including", "with"]):
            profile.semantic_complexity += 15
        
        # Question depth
        question_words = ["how", "why", "what if", "should", "design", "plan", "create"]
        for qw in question_words:
            if qw in query_lower:
                profile.semantic_complexity += 10
                break
        
        profile.semantic_complexity = min(100, profile.semantic_complexity)
        
        # 2. Domain breadth
        active_axes = sum(1 for v in axis_vector.values() if v)
        profile.domain_breadth = min(100, active_axes * 8)
        
        # Cross-domain indicators
        domain = context.get("domain", "").lower()
        sectors = context.get("sectors", [])
        if len(sectors) > 1:
            profile.domain_breadth += 20
        
        profile.domain_breadth = min(100, profile.domain_breadth)
        
        # 3. Risk level (Axis 14)
        if any(kw in query_lower for kw in self.HIGH_RISK_DOMAINS):
            profile.risk_level += 40
        
        if any(kw in query_lower for kw in self.SAFETY_KEYWORDS):
            profile.risk_level += 40
        
        if context.get("high_stakes") or context.get("critical"):
            profile.risk_level += 30
        
        profile.risk_level = min(100, profile.risk_level)
        
        # 4. Regulatory intensity (Axes 6-7)
        if any(kw in query_lower for kw in self.REGULATED_KEYWORDS):
            profile.regulatory_intensity += 50
        
        if axis_vector.get(6) or axis_vector.get(7):
            profile.regulatory_intensity += 30
        
        if domain in ("healthcare", "finance", "defense", "government"):
            profile.regulatory_intensity += 20
        
        profile.regulatory_intensity = min(100, profile.regulatory_intensity)
        
        # 5. Novelty (Axis 17)
        # Non-security hash used only for novelty/dedup tracking.
        query_hash = hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()[:16]
        if query_hash not in self._query_hashes:
            profile.novelty_score = 30
            self._query_hashes.add(query_hash)
        
        # High novelty for complex new topics
        if profile.domain_breadth > 50 and profile.novelty_score > 0:
            profile.novelty_score += 20
        
        return profile
    
    def _select_tier(
        self,
        profile: ComplexityProfile,
        context: Dict[str, Any]
    ) -> ExecutionTier:
        """Select tier based on complexity profile."""
        max_score = profile.max_score()
        
        # Force higher tiers for specific conditions
        if context.get("force_tier"):
            try:
                return ExecutionTier(context["force_tier"])
            except ValueError:
                pass
        
        # Safety-critical always Tier 5
        if profile.risk_level >= 90:
            return ExecutionTier.TIER_5_CRITICAL
        
        # Regulated always at least Tier 4
        if profile.regulatory_intensity >= 80:
            return ExecutionTier.TIER_4_REGULATED
        
        # Select by threshold
        for threshold, tier in sorted(self.TIER_THRESHOLDS.items()):
            if max_score <= threshold:
                return tier
        
        return ExecutionTier.TIER_5_CRITICAL
    
    def _select_personas(
        self,
        tier: ExecutionTier,
        profile: ComplexityProfile
    ) -> List[str]:
        """Select required personas based on tier."""
        if tier == ExecutionTier.TIER_1_BYPASS:
            return []
        elif tier == ExecutionTier.TIER_2_LIGHT:
            return ["P8", "P9"]
        elif tier == ExecutionTier.TIER_3_STANDARD:
            personas = ["P8", "P9"]
            if profile.regulatory_intensity > 30:
                personas.append("P10")
            if profile.risk_level > 30:
                personas.append("P11")
            return personas
        else:
            # Tier 4-5: Full quad
            return ["P8", "P9", "P10", "P11"]
    
    def _generate_reasons(
        self,
        profile: ComplexityProfile,
        tier: ExecutionTier
    ) -> List[str]:
        """Generate human-readable decision reasons."""
        reasons = []
        
        if profile.risk_level >= 50:
            reasons.append(f"High risk detected (score={profile.risk_level:.0f})")
        
        if profile.regulatory_intensity >= 50:
            reasons.append(f"Regulatory context triggered (score={profile.regulatory_intensity:.0f})")
        
        if profile.semantic_complexity >= 60:
            reasons.append(f"Complex query structure (score={profile.semantic_complexity:.0f})")
        
        if profile.domain_breadth >= 50:
            reasons.append(f"Multi-domain scope (score={profile.domain_breadth:.0f})")
        
        if profile.novelty_score >= 30:
            reasons.append("Novel query detected")
        
        reasons.append(f"Selected tier: {tier.name_short}")
        
        return reasons
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get QAS metrics."""
        return {
            "total_queries": self._total_queries,
            "tier_distribution": {
                t.name_short: count 
                for t, count in self._tier_distribution.items()
            }
        }


# =============================================================================
# Factory
# =============================================================================

def create_query_analysis_system(config: Dict[str, Any] = None) -> QueryAnalysisSystem:
    """Create and configure a QueryAnalysisSystem instance."""
    return QueryAnalysisSystem(config)
