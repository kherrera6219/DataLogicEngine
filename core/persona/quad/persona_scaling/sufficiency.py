"""Persona sufficiency decision logic for quad-persona expansion."""

import logging
from typing import Any, Dict, List

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

        if "thresholds" in self.config:
            self.THRESHOLDS.update(self.config["thresholds"])

        if "pod_caps" in self.config:
            self.POD_CAPS.update(self.config["pod_caps"])

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
        thresholds = self.THRESHOLDS[threshold_mode]
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
            self.POD_CAPS["knowledge_max"],
        )
        plan.spawn_counts["sector"] = min(
            len(detected_subsystems.get("sector", [])),
            self.POD_CAPS["sector_max"],
        )
        plan.spawn_counts["regulatory"] = min(
            len(detected_subsystems.get("regulatory", [])),
            self.POD_CAPS["regulatory_max"],
        )
        plan.spawn_counts["compliance"] = min(
            len(detected_subsystems.get("compliance", [])),
            self.POD_CAPS["compliance_max"],
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
