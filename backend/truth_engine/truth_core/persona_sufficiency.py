import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class SufficiencyMode(Enum):
    QUAD_ONLY = "quad_only"
    EXPANDED_COMMITTEE = "expanded_committee"

class PersonaSufficiencyTool:
    """
    Decides per-query whether the base 4 personas are sufficient or if more specialists are needed.
    Implements a scoring gate based on:
    1. Complexity Score (Pillars/Sectors activated)
    2. Stake/Assurance Score (Defense, Safety Critical)
    3. Conflict Score (Disagreement level)
    4. Coverage Score (Unknowns/Missing info)
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or {
            'complexity': 0.7,
            'stake': 0.8,
            'conflict': 0.5,
            'coverage': 0.6
        }
        # Max caps per lane
        self.caps = {
            "knowledge": 6,
            "sector": 6,
            "regulatory": 3,
            "compliance": 3
        }

    def evaluate(self, 
                 query: str, 
                 mapped_axes: List[int], 
                 initial_outputs: Dict[str, Any], 
                 metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates sufficiency and returns a decision object.
        """
        scores = self._calculate_scores(query, mapped_axes, initial_outputs, metadata)
        
        reasons = []
        spawn = {"knowledge": 0, "sector": 0, "regulatory": 0, "compliance": 0}
        mode = SufficiencyMode.QUAD_ONLY

        # Decision Logic
        if scores['stake'] >= self.thresholds['stake']:
            mode = SufficiencyMode.EXPANDED_COMMITTEE
            reasons.append(f"High stakes/assurance detected: {metadata.get('domain', 'general')}")
            spawn['knowledge'] += 2
            spawn['sector'] += 2
            spawn['regulatory'] += 1
            spawn['compliance'] += 1

        if scores['complexity'] >= self.thresholds['complexity']:
            mode = SufficiencyMode.EXPANDED_COMMITTEE
            reasons.append(f"High cross-domain complexity ({len(mapped_axes)} axes)")
            spawn['knowledge'] += 2
            spawn['sector'] += 2

        if scores['conflict'] >= self.thresholds['conflict']:
            mode = SufficiencyMode.EXPANDED_COMMITTEE
            reasons.append("High unresolved conflict in initial quad output")
            spawn['knowledge'] += 1
            spawn['sector'] += 1
            spawn['regulatory'] += 1
            spawn['compliance'] += 1

        if scores['coverage'] < self.thresholds['coverage']:
            mode = SufficiencyMode.EXPANDED_COMMITTEE
            reasons.append("Insufficient coverage/certainty in base persona reports")
            spawn['knowledge'] += 1
            spawn['sector'] += 1

        # Apply Caps
        for lane in spawn:
            spawn[lane] = min(spawn[lane], self.caps[f"{lane}_max"] if f"{lane}_max" in self.caps else self.caps[lane])

        return {
            "mode": mode.value,
            "spawn": spawn,
            "reasons": reasons,
            "scores": scores,
            "caps": self.caps,
            "stop_conditions": [
                "confidence >= 0.995",
                "no unresolved conflicts remain",
                "coverage score >= threshold per lane"
            ]
        }

    def _calculate_scores(self, 
                          query: str, 
                          mapped_axes: List[int], 
                          initial_outputs: Dict[str, Any], 
                          metadata: Dict[str, Any]) -> Dict[str, float]:
        """Calculates normalized scores for the gating logic."""
        # Complexity: 17 axes max
        complexity = min(len(mapped_axes) / 8.0, 1.0) 
        
        # Stake: based on metadata tags
        high_stake_tags = ['defense', 'aerospace', 'medical', 'critical_infra']
        stake = 1.0 if any(tag in metadata.get('tags', []) for tag in high_stake_tags) else 0.4
        
        # Conflict: Placeholder for real variance check between personas
        # In a real system, this would measure semantic distance between persona outputs
        conflict = metadata.get('initial_conflict_rating', 0.3)
        
        # Coverage: Check for 'unknown' or 'missing' flags in reports
        coverage = metadata.get('initial_coverage_rating', 0.8)

        return {
            'complexity': complexity,
            'stake': stake,
            'conflict': conflict,
            'coverage': coverage
        }
