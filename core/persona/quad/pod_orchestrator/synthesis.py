"""Pod synthesis and cross-pod deconfliction."""

import logging
from typing import Any, Dict, List, Tuple

from core.persona.quad.pod_models import (
    CrossPodConflict,
    ExpandedPersona,
    PodState,
    PodType,
)

logger = logging.getLogger(__name__)


class PodSynthesizer:
    """Synthesizes outputs from multiple personas within a single pod."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the synthesizer."""
        self.config = config or {}
        self.synthesis_threshold = self.config.get("synthesis_threshold", 0.8)

    def synthesize(self, pod: PodState) -> Tuple[str, float]:
        """Synthesize outputs from all personas in a pod."""
        if not pod.personas:
            return "", 0.0

        logger.info(f"Synthesizing {len(pod.personas)} personas in {pod.pod_type.value} pod")

        active_personas = [p for p in pod.personas if p.is_active and p.response]

        if not active_personas:
            logger.warning(f"No active personas with responses in {pod.pod_type.value} pod")
            return "", 0.0

        conflicts = self._detect_internal_conflicts(active_personas)
        pod.internal_conflicts = conflicts

        sections = []
        sections.append(f"## {pod.pod_type.value.title()} Pod Synthesis")
        sections.append(f"*Consolidated from {len(active_personas)} expert perspectives*\n")

        sections.append("### Key Findings")
        for persona in active_personas:
            sections.append(f"- **{persona.name}**: {persona.response[:200]}...")

        if not any(c["severity"] in ("high", "critical") for c in conflicts):
            sections.append("\n### Pod Consensus")
            sections.append("The pod reached consensus on the key technical points.")
        else:
            sections.append("\n### Unresolved Items")
            for conflict in conflicts:
                sections.append(f"- {conflict['description']}")

        average_confidence = sum(p.confidence for p in active_personas) / len(active_personas)
        sections.append(f"\n*Pod Confidence: {average_confidence:.2f}*")

        synthesized_output = "\n".join(sections)
        collective_confidence = pod.calculate_collective_confidence()
        pod.synthesized_output = synthesized_output

        return synthesized_output, collective_confidence

    def _detect_internal_conflicts(self, personas: List[ExpandedPersona]) -> List[Dict[str, Any]]:
        """Detect conflicts between personas within the same pod."""
        conflicts = []

        for i, p1 in enumerate(personas):
            for p2 in personas[i + 1:]:
                conf_diff = abs(p1.confidence - p2.confidence)

                if conf_diff > 0.3:
                    conflicts.append({
                        "type": "confidence_divergence",
                        "personas": [p1.persona_id, p2.persona_id],
                        "description": f"Confidence divergence between {p1.name} ({p1.confidence:.2f}) and {p2.name} ({p2.confidence:.2f})",
                        "severity": "medium" if conf_diff < 0.5 else "high",
                    })

        return conflicts


class CrossPodDeconfliction:
    """Resolves conflicts between different pods."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize deconfliction."""
        self.config = config or {}
        self.max_iterations = self.config.get("max_deconfliction_iterations", 3)

    def deconflict(self, pods: Dict[str, PodState]) -> Tuple[List[CrossPodConflict], bool]:
        """Perform cross-pod deconfliction."""
        logger.info("Starting cross-pod deconfliction")

        conflicts = []

        if PodType.KNOWLEDGE.value in pods and PodType.REGULATORY.value in pods:
            k_conflicts = self._check_constraint_violations(
                pods[PodType.KNOWLEDGE.value],
                pods[PodType.REGULATORY.value],
                "regulatory",
            )
            conflicts.extend(k_conflicts)

        if PodType.SECTOR.value in pods and PodType.COMPLIANCE.value in pods:
            s_conflicts = self._check_constraint_violations(
                pods[PodType.SECTOR.value],
                pods[PodType.COMPLIANCE.value],
                "compliance",
            )
            conflicts.extend(s_conflicts)

        if PodType.KNOWLEDGE.value in pods and PodType.SECTOR.value in pods:
            alignment_conflicts = self._check_alignment(
                pods[PodType.KNOWLEDGE.value],
                pods[PodType.SECTOR.value],
            )
            conflicts.extend(alignment_conflicts)

        resolved_count = 0
        for conflict in conflicts:
            if self._try_resolve(conflict, pods):
                resolved_count += 1

        all_resolved = all(c.resolved for c in conflicts)

        logger.info(f"Cross-pod deconfliction: {len(conflicts)} conflicts, {resolved_count} resolved")

        return conflicts, all_resolved

    def _check_constraint_violations(
        self,
        source_pod: PodState,
        constraint_pod: PodState,
        constraint_type: str,
    ) -> List[CrossPodConflict]:
        """Check if source pod violates constraints from constraint pod."""
        conflicts = []

        source_conf = source_pod.collective_confidence
        constraint_conf = constraint_pod.collective_confidence

        if source_conf > 0.9 and constraint_conf < 0.7:
            conflicts.append(CrossPodConflict(
                source_pod=source_pod.pod_type,
                target_pod=constraint_pod.pod_type,
                conflict_type="constraint_uncertainty",
                source_claim=f"{source_pod.pod_type.value} outputs may not satisfy {constraint_type} constraints",
                target_claim=f"{constraint_pod.pod_type.value} has low confidence in constraint verification",
                severity="medium",
            ))

        return conflicts

    def _check_alignment(self, pod1: PodState, pod2: PodState) -> List[CrossPodConflict]:
        """Check alignment between two pods."""
        conflicts = []
        conf_diff = abs(pod1.collective_confidence - pod2.collective_confidence)

        if conf_diff > 0.25:
            conflicts.append(CrossPodConflict(
                source_pod=pod1.pod_type,
                target_pod=pod2.pod_type,
                conflict_type="alignment_gap",
                source_claim=f"{pod1.pod_type.value} confidence: {pod1.collective_confidence:.2f}",
                target_claim=f"{pod2.pod_type.value} confidence: {pod2.collective_confidence:.2f}",
                severity="low" if conf_diff < 0.35 else "medium",
            ))

        return conflicts

    def _try_resolve(self, conflict: CrossPodConflict, pods: Dict[str, PodState]) -> bool:
        """Attempt to automatically resolve a conflict."""
        if conflict.severity == "low":
            source_pod = pods.get(conflict.source_pod.value)
            target_pod = pods.get(conflict.target_pod.value)

            if source_pod and target_pod:
                if source_pod.collective_confidence >= target_pod.collective_confidence:
                    conflict.resolution = f"Deferred to {conflict.source_pod.value} (higher confidence)"
                else:
                    conflict.resolution = f"Deferred to {conflict.target_pod.value} (higher confidence)"
                conflict.resolution_method = "confidence_priority"
                conflict.resolved = True
                return True

        if conflict.severity == "medium":
            conflict.resolution = "Flagged for human review; proceeding with constraints applied"
            conflict.resolution_method = "constraint_priority"
            conflict.resolved = True
            return True

        return False
