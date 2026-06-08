"""Persona sufficiency decision logic for quad-persona expansion."""

import logging
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Optional

from core.persona.quad.pod_models import (
    ExpansionPlan,
    ScalingDecision,
    SubsystemProfile,
    SufficiencySignals,
)
from core.persona.quad.persona_scaling.profiles import (
    COMPLIANCE_PROFILES,
    DEFENSE_SUBSYSTEM_PROFILES,
    REGULATORY_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES,
)

logger = logging.getLogger(__name__)


class HighAssuranceDetector:
    """Detects if a query requires high-assurance mode based on domain signals."""

    DEFENSE_KEYWORDS = {
        "weapon", "military", "defense", "dod", "classified", "secret",
        "combat", "warfighter", "tactical", "fighter", "bomber", "missile",
        "f-22", "f-35", "b-21", "c-17", "aegis", "patriot", "thaad",
        "army", "navy", "air force", "marines", "space force",
    }

    SAFETY_CRITICAL_KEYWORDS = {
        "safety", "safety-critical", "flight safety", "airworthiness",
        "do-178", "do-254", "arp4754", "hazard", "catastrophic",
        "medical device", "fda", "life-critical", "patient safety",
    }

    EXPORT_CONTROL_KEYWORDS = {
        "itar", "ear", "export control", "export license", "foreign national",
        "technology control", "classified", "cui", "fouo", "noforn",
    }

    PROGRAM_KEYWORDS = {
        "modernization", "upgrade", "fielding", "program", "acquisition",
        "milestone", "production", "deployment", "sustainment",
    }

    @classmethod
    def detect(cls, query: str, context: Dict[str, Any] = None) -> Dict[str, bool]:
        """Detect high-assurance signals in query and context."""
        query_lower = query.lower()
        context = context or {}

        is_defense = any(kw in query_lower for kw in cls.DEFENSE_KEYWORDS)
        is_safety_critical = any(kw in query_lower for kw in cls.SAFETY_CRITICAL_KEYWORDS)
        has_export_control = any(kw in query_lower for kw in cls.EXPORT_CONTROL_KEYWORDS)
        is_major_program = any(kw in query_lower for kw in cls.PROGRAM_KEYWORDS)

        domain = context.get("domain", "").lower()
        sector = context.get("sector", "").lower()

        if domain in ("defense", "military", "aerospace"):
            is_defense = True
        if sector in ("government", "defense", "aerospace"):
            is_defense = True

        is_high_assurance = is_defense or is_safety_critical or has_export_control

        return {
            "is_high_assurance": is_high_assurance,
            "is_defense_domain": is_defense,
            "has_safety_critical": is_safety_critical,
            "has_export_control": has_export_control,
            "is_major_program": is_major_program,
        }


class SubsystemDetector:
    """Detects subsystems mentioned in a query for persona specialization."""

    @classmethod
    def detect_subsystems(
        cls,
        query: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, List[SubsystemProfile]]:
        """Detect subsystems in query and return matching profiles by pod type."""
        query_lower = query.lower()

        detected = {
            "knowledge": [],
            "sector": [],
            "regulatory": [],
            "compliance": [],
        }

        for key, profile in DEFENSE_SUBSYSTEM_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["knowledge"].append(profile)

        for key, profile in SECTOR_SUBSYSTEM_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["sector"].append(profile)

        for key, profile in REGULATORY_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["regulatory"].append(profile)

        for key, profile in COMPLIANCE_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["compliance"].append(profile)

        return detected


class PersonaSufficiencyTool:
    """Determines if base Quad Persona is sufficient or expansion is needed."""

    THRESHOLDS = {
        "standard": {
            "complexity": 60,
            "stakes": 40,
            "conflict": 0.2,
            "coverage": 0.85,
        },
        "high_assurance": {
            "complexity": 40,
            "stakes": 30,
            "conflict": 0.1,
            "coverage": 0.95,
        },
    }

    POD_CAPS = {
        "knowledge_max": 6,
        "sector_max": 6,
        "regulatory_max": 3,
        "compliance_max": 3,
    }

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the sufficiency tool."""
        self.config = config or {}
        self.thresholds = deepcopy(self.THRESHOLDS)
        self.pod_caps = deepcopy(self.POD_CAPS)

        if "thresholds" in self.config:
            self.thresholds.update(deepcopy(self.config["thresholds"]))

        if "pod_caps" in self.config:
            self.pod_caps.update(deepcopy(self.config["pod_caps"]))

        logger.info("PersonaSufficiencyTool initialized")

    def evaluate(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        persona_results: Dict[str, Dict[str, Any]],
    ) -> ScalingDecision:
        """Evaluate if base quad personas are sufficient."""
        logger.info(f"Evaluating persona sufficiency for query: {query[:50]}...")

        ha_signals = HighAssuranceDetector.detect(query, context)
        detected_subsystems = SubsystemDetector.detect_subsystems(query, context)

        signals = self._compute_signals(
            query,
            context,
            axis_vector,
            persona_results,
            ha_signals,
            detected_subsystems,
        )

        threshold_mode = "high_assurance" if signals.is_high_assurance else "standard"
        thresholds = self.thresholds[threshold_mode]
        should_expand = signals.exceeds_thresholds(thresholds)

        if not should_expand:
            logger.info("Quad-only mode: All signals within thresholds")
            return ScalingDecision(
                mode="quad_only",
                signals=signals,
                expansion_plan=None,
                threshold_mode=threshold_mode,
                thresholds_used=thresholds,
            )

        expansion_plan = self._calculate_expansion_plan(signals, detected_subsystems, thresholds)

        logger.info(f"Expanded committee mode: Spawning {expansion_plan.total_personas} additional personas")

        return ScalingDecision(
            mode="expanded_committee",
            signals=signals,
            expansion_plan=expansion_plan,
            threshold_mode=threshold_mode,
            thresholds_used=thresholds,
        )

    def _compute_signals(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        persona_results: Dict[str, Dict[str, Any]],
        ha_signals: Dict[str, bool],
        detected_subsystems: Dict[str, List[SubsystemProfile]],
    ) -> SufficiencySignals:
        """Compute all sufficiency signals."""
        signals = SufficiencySignals()

        signals.is_high_assurance = ha_signals.get("is_high_assurance", False)
        signals.is_defense_domain = ha_signals.get("is_defense_domain", False)
        signals.has_safety_critical = ha_signals.get("has_safety_critical", False)
        signals.has_export_control = ha_signals.get("has_export_control", False)

        signals.subsystems_detected = sum(len(v) for v in detected_subsystems.values())
        signals.complexity_score = self._compute_complexity_score(query, context, axis_vector, detected_subsystems)
        signals.stakes_score = self._compute_stakes_score(query, context, ha_signals)
        signals.conflict_score = self._compute_conflict_score(persona_results)
        signals.coverage_score = self._compute_coverage_score(persona_results)

        signals.pillars_activated = len([
            v for k, v in axis_vector.items()
            if k == 1 and v
        ])
        signals.sectors_activated = len([
            v for k, v in axis_vector.items()
            if k == 2 and v
        ])

        return signals

    def _compute_complexity_score(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        detected_subsystems: Dict[str, List[SubsystemProfile]],
    ) -> float:
        """Compute complexity score (0-100)."""
        score = 0.0

        subsystem_count = sum(len(v) for v in detected_subsystems.values())
        score += min(40, subsystem_count * 8)

        active_axes = sum(1 for v in axis_vector.values() if v)
        score += min(20, active_axes * 2)

        words = query.split()
        if len(words) > 30:
            score += 10
        if len(words) > 50:
            score += 10

        cross_domain_keywords = ["and", "plus", "with", "including", "combined"]
        cross_count = sum(1 for kw in cross_domain_keywords if kw in query.lower())
        score += min(20, cross_count * 5)

        return min(100, score)

    def _compute_stakes_score(
        self,
        query: str,
        context: Dict[str, Any],
        ha_signals: Dict[str, bool],
    ) -> float:
        """Compute stakes score (0-100)."""
        score = 0.0

        if ha_signals.get("is_high_assurance"):
            score += 25
        if ha_signals.get("is_defense_domain"):
            score += 25
        if ha_signals.get("has_safety_critical"):
            score += 25
        if ha_signals.get("has_export_control"):
            score += 15
        if ha_signals.get("is_major_program"):
            score += 10

        return min(100, score)

    def _compute_conflict_score(self, persona_results: Dict[str, Dict[str, Any]]) -> float:
        """Compute conflict score (0-1) from persona results."""
        if not persona_results:
            return 0.0

        conflicts = 0
        total_pairs = 0
        persona_types = list(persona_results.keys())

        for i, pt1 in enumerate(persona_types):
            for pt2 in persona_types[i + 1:]:
                total_pairs += 1

                r1 = persona_results.get(pt1, {})
                r2 = persona_results.get(pt2, {})

                c1 = r1.get("confidence", 0.5)
                c2 = r2.get("confidence", 0.5)

                if abs(c1 - c2) > 0.3:
                    conflicts += 0.5

                if r1.get("disagrees_with") or r2.get("disagrees_with"):
                    conflicts += 0.5

        if total_pairs == 0:
            return 0.0

        return min(1.0, conflicts / total_pairs)

    def _compute_coverage_score(self, persona_results: Dict[str, Dict[str, Any]]) -> float:
        """Compute coverage score (0-1) from persona results."""
        if not persona_results:
            return 0.5

        coverages = []

        for persona_type, result in persona_results.items():
            confidence = result.get("confidence", 0.5)

            if result.get("has_gaps"):
                confidence *= 0.8
            if result.get("needs_more_info"):
                confidence *= 0.9

            coverages.append(confidence)

        return sum(coverages) / len(coverages) if coverages else 0.5

    def _calculate_expansion_plan(
        self,
        signals: SufficiencySignals,
        detected_subsystems: Dict[str, List[SubsystemProfile]],
        thresholds: Dict[str, float],
    ) -> ExpansionPlan:
        """Calculate how many personas to spawn in each pod."""
        plan = ExpansionPlan()
        plan.reasons = signals.get_expansion_reasons(thresholds)

        plan.spawn_counts["knowledge"] = min(
            len(detected_subsystems.get("knowledge", [])),
            self.pod_caps["knowledge_max"],
        )
        plan.spawn_counts["sector"] = min(
            len(detected_subsystems.get("sector", [])),
            self.pod_caps["sector_max"],
        )
        plan.spawn_counts["regulatory"] = min(
            len(detected_subsystems.get("regulatory", [])),
            self.pod_caps["regulatory_max"],
        )
        plan.spawn_counts["compliance"] = min(
            len(detected_subsystems.get("compliance", [])),
            self.pod_caps["compliance_max"],
        )

        if signals.complexity_score > 70:
            plan.spawn_counts["knowledge"] = max(plan.spawn_counts["knowledge"], 3)
            plan.spawn_counts["sector"] = max(plan.spawn_counts["sector"], 2)

        if signals.stakes_score > 60:
            plan.spawn_counts["regulatory"] = max(plan.spawn_counts["regulatory"], 2)
            plan.spawn_counts["compliance"] = max(plan.spawn_counts["compliance"], 2)

        plan.subsystems_to_spawn = {
            pod: [p.subsystem_id for p in profiles]
            for pod, profiles in detected_subsystems.items()
        }

        return plan


def create_sufficiency_tool(config: Dict[str, Any] = None) -> PersonaSufficiencyTool:
    """Create and configure a PersonaSufficiencyTool instance."""
    return PersonaSufficiencyTool(config)


# ---------------------------------------------------------------------------
# Gateway-pipeline sufficiency adapter (DUP-5 consolidated from
# backend.truth_engine.truth_core.persona_sufficiency — Sprint 5).
#
# GatewayPersonaSufficiencyTool exposes a lighter, dict-based API used by
# the LLM gateway (backend.llm_gateway.gateway) and TruthCore engine
# (backend.truth_engine.truth_core.engine). It is intentionally distinct
# from PersonaSufficiencyTool above: the gateway pipeline passes
# mapped_axes: List[int] and expects a plain dict return rather than a
# ScalingDecision object, making a direct substitution unsuitable without
# rewriting all callers and the persona_scaling_bridge.
# ---------------------------------------------------------------------------

class SufficiencyMode(Enum):
    """Mode values returned by GatewayPersonaSufficiencyTool."""
    QUAD_ONLY = "quad_only"
    EXPANDED_COMMITTEE = "expanded_committee"


class GatewayPersonaSufficiencyTool:
    """
    Gateway-path sufficiency gate: decides per-query whether the base 4
    personas are sufficient or if more specialists are needed.

    Distinct from PersonaSufficiencyTool (the Phase 5 canonical above). This
    class uses a lighter dict-based API and is called directly by the LLM
    gateway and truth_core engine via persona_scaling_bridge.

    Consolidated here from backend.truth_engine.truth_core.persona_sufficiency
    as part of DUP-5 resolution (Sprint 5). The backend copy is deleted;
    import from this canonical location instead.

    Scoring gates:
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
            'coverage': 0.6,
        }
        # Max caps per lane
        self.caps = {
            "knowledge": 6,
            "sector": 6,
            "regulatory": 3,
            "compliance": 3,
        }

    def evaluate(
        self,
        query: str,
        mapped_axes: List[int],
        initial_outputs: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluates sufficiency with input hardening and resource protection."""
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

            reasons: List[str] = []
            spawn: Dict[str, int] = {"knowledge": 0, "sector": 0, "regulatory": 0, "compliance": 0}
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
                    "coverage score >= threshold per lane",
                ],
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
            "stop_conditions": ["standard_quad_verification"],
        }

    def _calculate_scores(
        self,
        query: str,
        mapped_axes: List[int],
        initial_outputs: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculates normalized scores based on real heuristics and initial quad variance."""
        # 1. Complexity Score: 17 axes maximum; > 50% of axes = high complexity
        complexity = min(len(mapped_axes) / 10.0, 1.0)

        # 2. Stake/Assurance Score: Keyword matching against high-stakes domains
        high_stake_tags = {'defense', 'aerospace', 'medical', 'critical_infra', 'regulatory', 'legal'}
        query_tags = set(metadata.get('tags', []))
        stake = 1.0 if query_tags.intersection(high_stake_tags) else 0.4

        # 3. Conflict Score: variance of initial quad confidence scores
        confidences = [p.get('confidence', 0.5) for p in initial_outputs.values() if isinstance(p, dict)]
        if len(confidences) > 1:
            mean_conf = sum(confidences) / len(confidences)
            variance = sum((x - mean_conf) ** 2 for x in confidences) / len(confidences)
            # Normalize variance to 0.0-1.0 (0.25 is max variance for 0.0-1.0 range)
            conflict = min(variance * 4.0, 1.0)
        else:
            conflict = 0.3  # Default low conflict if single-persona

        # 4. Coverage Score: density of addressable axes covered in initial quad reports
        total_axes_needed = set(mapped_axes)
        if not total_axes_needed:
            coverage = 1.0
        else:
            combined_analysis = " ".join(
                [str(p.get('response', '')) for p in initial_outputs.values() if isinstance(p, dict)]
            )
            axes_found = sum(
                1 for axis_id in total_axes_needed
                if f"Axis {axis_id}" in combined_analysis
                or f"coordinate {axis_id}" in combined_analysis.lower()
            )
            coverage = axes_found / len(total_axes_needed)

        return {
            'complexity': complexity,
            'stake': stake,
            'conflict': conflict,
            'coverage': coverage,
        }
