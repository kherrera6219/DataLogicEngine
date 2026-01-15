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
        Evaluates sufficiency with input hardening and resource protection.
        """
        # 1. Input Sanitization & Validation
        if not isinstance(query, str) or len(query) > 10000:
            logger.warning("Adversarial query length detected. Defaulting to QUAD_ONLY.")
            return self._fail_safe_decision("Query exceeds safety length")
        
        if not isinstance(mapped_axes, list) or len(mapped_axes) > 17:
            logger.warning("Invalid axis mapping detected. Defaulting to QUAD_ONLY.")
            return self._fail_safe_decision("Axis count exceeds system limits (17)")

        try:
            scores = self._calculate_scores(query, mapped_axes, initial_outputs, metadata)
            logger.info(f"Sufficiency Scores: {scores} (Tags: {metadata.get('tags')})")
            
            reasons = []
            spawn = {"knowledge": 0, "sector": 0, "regulatory": 0, "compliance": 0}
            mode = SufficiencyMode.QUAD_ONLY

            # 2. Hardened Decision Logic
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

            # 3. Strict Resource Capping
            for lane in spawn:
                max_cap = self.caps.get(f"{lane}_max", self.caps.get(lane, 3))
                spawn[lane] = min(spawn[lane], max_cap)

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
        except Exception as e:
            logger.error(f"Sufficiency validation failed: {e}")
            return self._fail_safe_decision(f"Internal error: {str(e)}")

    def _fail_safe_decision(self, reason: str) -> Dict[str, Any]:
        """Returns a safe default decision in case of calculation error or attack."""
        return {
            "mode": SufficiencyMode.QUAD_ONLY.value,
            "spawn": {"knowledge": 0, "sector": 0, "regulatory": 0, "compliance": 0},
            "reasons": [f"Fail-safe triggered: {reason}"],
            "scores": {},
            "caps": self.caps,
            "stop_conditions": ["standard_quad_verification"]
        }

    def _calculate_scores(self, 
                          query: str, 
                          mapped_axes: List[int], 
                          initial_outputs: Dict[str, Any], 
                          metadata: Dict[str, Any]) -> Dict[str, float]:
        """Calculates normalized scores based on real heuristics and initial quad variance."""
        
        # 1. Complexity Score: 17 axes maximum in the UKG standard
        # A query activating > 50% of the possible axes is considered high complexity
        complexity = min(len(mapped_axes) / 10.0, 1.0) 
        
        # 2. Stake/Assurance Score: Keyword matching against high-stakes domains
        high_stake_tags = {'defense', 'aerospace', 'medical', 'critical_infra', 'regulatory', 'legal'}
        query_tags = set(metadata.get('tags', []))
        stake = 1.0 if query_tags.intersection(high_stake_tags) else 0.4
        
        # 3. Conflict Score: Calculated as the variance/spread of initial quad confidence
        # If the 4 experts disagree significantly on their certainty, conflict is high.
        confidences = [p.get('confidence', 0.5) for p in initial_outputs.values() if isinstance(p, dict)]
        if len(confidences) > 1:
            mean_conf = sum(confidences) / len(confidences)
            variance = sum((x - mean_conf) ** 2 for x in confidences) / len(confidences)
            # Normalize variance to a 0.0-1.0 score (0.25 is max variance for 0.0-1.0 range)
            conflict = min(variance * 4.0, 1.0)
        else:
            conflict = 0.3 # Default low conflict if single-persona
            
        # 4. Coverage Score: Density of addressable axes covered in initial quad reports
        # We check if the specialists actually addressed the specific axes mapped to the query.
        total_axes_needed = set(mapped_axes)
        if not total_axes_needed:
            coverage = 1.0
        else:
            # Check how many 'found' tags or axis markers exist in the combined response
            combined_analysis = " ".join([str(p.get('response', '')) for p in initial_outputs.values() if isinstance(p, dict)])
            axes_found = 0
            for axis_id in total_axes_needed:
                if f"Axis {axis_id}" in combined_analysis or f"coordinate {axis_id}" in combined_analysis.lower():
                    axes_found += 1
            
            coverage = axes_found / len(total_axes_needed)

        return {
            'complexity': complexity,
            'stake': stake,
            'conflict': conflict,
            'coverage': coverage
        }
    
    def _fail_safe_decision(self, reason: str) -> Dict[str, Any]:
        """Returns a safe default decision (Quad-Only) in case of processing error."""
        return {
            "mode": SufficiencyMode.QUAD_ONLY.value,
            "spawn": {"knowledge": 0, "sector": 0, "regulatory": 0, "compliance": 0},
            "reasons": [f"Fail-safe engaged: {reason}"],
            "scores": {"meta": "failed"},
            "caps": self.caps,
            "stop_conditions": ["system_stability_reversion"]
        }
