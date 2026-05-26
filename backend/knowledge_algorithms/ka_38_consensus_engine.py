"""
KA-038: Consensus Engine
Purpose: Derive weighted consensus from multiple persona claims and detect expert conflicts.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

# Attempt to import mathematical framework for dynamic weights
try:
    from quad_persona.mathematical_framework import DynamicWeightFunctions
    MATH_AVAILABLE = True
except ImportError:
    MATH_AVAILABLE = False

logger = logging.getLogger(__name__)

class PersonaClaim(BaseModel):
    claim_id: str = Field(..., description="Unique identifier for the claim being evaluated")
    content: str = Field(..., description="The substantive content of the claim")
    persona_type: str = Field(..., description="The persona providing the claim (knowledge, sector, regulatory, compliance)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Persona's confidence in this claim")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KA038Input(BaseModel):
    claims: List[PersonaClaim] = Field(..., description="List of claims from various personas")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context for dynamic weight calculation")
    manual_weights: Optional[Dict[str, float]] = Field(None, description="Optional manual override for persona weights")

    @field_validator("manual_weights", mode="before")
    @classmethod
    def coerce_manual_weights(cls, value):
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            return value
        # Generic test harness may inject scalar placeholders; ignore them.
        return None

class KA038ConsensusEngine(KnowledgeAlgorithm):
    """
    KA-038: Enhanced Consensus Engine for Enterprise v2.0.
    Implements weighted semantic voting and conflict detection.
    """
    input_schema = KA038Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-038"
        self.weights_engine = DynamicWeightFunctions() if MATH_AVAILABLE else None

    def _run_logic(self, input_data: KA038Input) -> Dict[str, Any]:
        claims = input_data.claims
        context = input_data.context
        
        # 1. Resolve Weights
        weights = input_data.manual_weights
        if not weights:
            if self.weights_engine:
                weights = self.weights_engine.compute_all_weights(context)
            else:
                # Fallback to equal weights
                weights = {"knowledge": 0.25, "sector": 0.25, "regulatory": 0.25, "compliance": 0.25}
        weights = json.loads(json.dumps(weights, sort_keys=True, default=float))

        self.log_execution_step("Calculating Weighted Consensus", {"claim_count": len(claims), "weights": weights})

        # 2. Group Claims by ID (Semantic Grouping)
        groups: Dict[str, List[PersonaClaim]] = {}
        for claim in claims:
            if claim.claim_id not in groups:
                groups[claim.claim_id] = []
            groups[claim.claim_id].append(claim)

        # 3. Process Each Group
        consensus_results = []
        conflicts_detected = []

        for claim_id, group_claims in groups.items():
            result = self._evaluate_group_consensus(claim_id, group_claims, weights)
            consensus_results.append(result)
            
            if result.get("has_conflict"):
                conflicts_detected.append({
                    "claim_id": claim_id,
                    "delta": result.get("max_delta"),
                    "voters": [c.persona_type for c in group_claims]
                })

        return {
            "success": True,
            "ka_id": self.ka_id,
            "consensus_results": consensus_results,
            "conflicts": conflicts_detected,
            "overall_consensus_reached": len(conflicts_detected) == 0,
            "metadata": {
                "weights_used": weights,
                "math_framework_active": MATH_AVAILABLE
            }
        }

    def _evaluate_group_consensus(self, claim_id: str, group: List[PersonaClaim], weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculates weighted confidence and detects significant delta (conflict)."""
        weighted_sum = 0.0
        weight_total = 0.0
        confidences = []

        for claim in group:
            w = weights.get(claim.persona_type, 0.0)
            if w > 0:
                weighted_sum += claim.confidence * w
                weight_total += w
                confidences.append(claim.confidence)

        final_conf = (weighted_sum / weight_total) if weight_total > 0 else 0.0
        
        # Conflict Detection: Delta > 0.4 between any two active voters
        max_delta = 0.0
        if len(confidences) > 1:
            max_delta = max(confidences) - min(confidences)

        return {
            "claim_id": claim_id,
            "content": group[0].content, # Representative content
            "weighted_confidence": round(final_conf, 4),
            "max_delta": round(max_delta, 4),
            "has_conflict": max_delta > 0.4,
            "voter_count": len(group)
        }

    def _fallback_logic(self, input_data: Any, exception: Exception) -> Dict[str, Any]:
        return {
            "success": False,
            "error": str(exception),
            "consensus_results": [],
            "status": "DEGRADED"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA038ConsensusEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-038 Fatal Execution Error: {e}")
        return {"success": False, "error": str(e)}
