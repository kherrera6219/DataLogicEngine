"""Main orchestration flow for expanded persona pods."""

import logging
import random
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

from core.persona.quad.pod_models import (
    ExpandedPersona,
    ExpansionPlan,
    PodState,
    PodType,
    ScalingDecision,
    ScalingOrchestrationState,
)
from core.persona.quad.pod_orchestrator.builder import PersonaBuilder
from core.persona.quad.pod_orchestrator.synthesis import (
    CrossPodDeconfliction,
    PodSynthesizer,
)

logger = logging.getLogger(__name__)


class PodOrchestrator:
    """Main orchestrator for persona pod execution."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the orchestrator."""
        self.config = config or {}

        self.synthesizer = PodSynthesizer(config)
        self.deconfliction = CrossPodDeconfliction(config)

        self.max_workers = self.config.get("max_workers", 4)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.995)

        logger.info("PodOrchestrator initialized")

    def orchestrate(
        self,
        query: str,
        context: Dict[str, Any],
        scaling_decision: ScalingDecision,
        base_persona_results: Dict[str, Dict[str, Any]] = None,
    ) -> ScalingOrchestrationState:
        """Execute full pod orchestration."""
        logger.info("Starting pod orchestration")

        state = ScalingOrchestrationState(
            query_id=context.get("query_id", str(uuid.uuid4())),
            query_text=query,
            scaling_decision=scaling_decision,
        )

        state.update_status("processing", "pod_spawning")

        if not scaling_decision.should_expand:
            logger.info("Quad-only mode: Skipping pod expansion")
            state.update_status("completed", "quad_only")
            state.final_confidence = self._calculate_base_confidence(base_persona_results)
            state.threshold_met = state.final_confidence >= self.confidence_threshold
            return state

        try:
            pods = self._spawn_pods(scaling_decision.expansion_plan, context)
            for pod in pods:
                state.add_pod(pod)

            state.update_status("processing", "persona_processing")
            self._process_all_pods(state, query, context)

            state.update_status("processing", "within_pod_synthesis")
            for pod in state.pods.values():
                self.synthesizer.synthesize(pod)
                pod.update_status("completed")

            state.update_status("processing", "cross_pod_deconfliction")
            conflicts, all_resolved = self.deconfliction.deconflict(state.pods)
            state.cross_pod_conflicts = conflicts
            state.deconfliction_passes = 1

            while not all_resolved and state.deconfliction_passes < state.max_deconfliction_passes:
                state.deconfliction_passes += 1
                conflicts, all_resolved = self.deconfliction.deconflict(state.pods)
                state.cross_pod_conflicts = conflicts

            state.update_status("processing", "final_synthesis")
            state.final_synthesis = self._create_final_synthesis(state)
            state.final_confidence = self._calculate_final_confidence(state)
            state.threshold_met = state.final_confidence >= self.confidence_threshold

            state.update_status("completed", "success")

        except Exception as e:
            logger.error(f"Pod orchestration failed: {e}")
            state.update_status("failed", str(e))
            raise

        return state

    def _spawn_pods(self, expansion_plan: ExpansionPlan, context: Dict[str, Any]) -> List[PodState]:
        """Spawn pods based on expansion plan."""
        pods = []

        for pod_type in PodType:
            spawn_count = expansion_plan.spawn_counts.get(pod_type.value, 0)

            if spawn_count == 0:
                continue

            pod = PodState(pod_type=pod_type)
            subsystems = expansion_plan.subsystems_to_spawn.get(pod_type.value, [])

            for i, subsystem_id in enumerate(subsystems[:spawn_count]):
                persona = PersonaBuilder.build_persona(pod_type, subsystem_id, context)
                if persona:
                    pod.add_persona(persona)

            while pod.persona_count < spawn_count:
                default_persona = PersonaBuilder.build_default_persona(
                    pod_type,
                    pod.persona_count,
                    context,
                )
                pod.add_persona(default_persona)

            pods.append(pod)
            logger.info(f"Spawned {pod_type.value} pod with {pod.persona_count} personas")

        return pods

    def _process_all_pods(
        self,
        state: ScalingOrchestrationState,
        query: str,
        context: Dict[str, Any],
    ):
        """Process all personas across all pods."""
        all_tasks = []
        for pod in state.pods.values():
            for persona in pod.personas:
                all_tasks.append((pod, persona, query, context))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_single_persona, task): task
                for task in all_tasks
            }

            for future in as_completed(futures):
                pod, persona, _, _ = futures[future]
                try:
                    response, confidence = future.result()
                    pod.set_persona_response(persona.persona_id, response, confidence)
                except Exception as e:
                    logger.error(f"Persona processing failed: {e}")
                    persona.is_active = False

    def _process_single_persona(
        self,
        task: Tuple[PodState, ExpandedPersona, str, Dict[str, Any]],
    ) -> Tuple[str, float]:
        """Process a single persona's response."""
        pod, persona, query, context = task

        start_time = datetime.now(UTC)
        response = self._generate_persona_response(persona, query, context)
        confidence = self._calculate_persona_confidence(persona, query, context)

        end_time = datetime.now(UTC)
        persona.processing_time_ms = (end_time - start_time).total_seconds() * 1000

        return response, confidence

    def _generate_persona_response(
        self,
        persona: ExpandedPersona,
        query: str,
        context: Dict[str, Any],
    ) -> str:
        """Generate response for a persona (simulated for now)."""
        return f"[{persona.name}] Analysis of: {query[:100]}... " \
               f"Based on expertise in {persona.description}."

    def _calculate_persona_confidence(
        self,
        persona: ExpandedPersona,
        query: str,
        context: Dict[str, Any],
    ) -> float:
        """Calculate confidence for persona response."""
        base_confidence = {
            PodType.KNOWLEDGE: 0.85,
            PodType.SECTOR: 0.82,
            PodType.REGULATORY: 0.88,
            PodType.COMPLIANCE: 0.86,
        }.get(persona.pod_type, 0.80)

        if persona.subsystem_profile:
            base_confidence += 0.05

        variation = random.uniform(-0.05, 0.05)

        return min(0.99, max(0.5, base_confidence + variation))

    def _calculate_base_confidence(self, base_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate confidence from base quad results."""
        if not base_results:
            return 0.5

        confidences = [r.get("confidence", 0.5) for r in base_results.values()]
        return sum(confidences) / len(confidences)

    def _calculate_final_confidence(self, state: ScalingOrchestrationState) -> float:
        """Calculate final confidence from orchestration state."""
        if not state.pods:
            return 0.5

        weights = {
            PodType.KNOWLEDGE.value: 0.30,
            PodType.SECTOR.value: 0.25,
            PodType.REGULATORY.value: 0.25,
            PodType.COMPLIANCE.value: 0.20,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for pod_type, pod in state.pods.items():
            weight = weights.get(pod_type, 0.25)
            weighted_sum += pod.collective_confidence * weight
            total_weight += weight

        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5

        unresolved = sum(1 for c in state.cross_pod_conflicts if not c.resolved)
        penalty = unresolved * 0.02

        return max(0.5, base_confidence - penalty)

    def _create_final_synthesis(self, state: ScalingOrchestrationState) -> str:
        """Create final synthesized output from all pods."""
        sections = []

        sections.append("# Expanded Committee Response")
        sections.append(f"*Query: {state.query_text[:100]}...*\n")

        for pod_type, pod in state.pods.items():
            sections.append(f"## {pod_type.title()} Expert Pod")
            sections.append(f"- Personas: {pod.persona_count}")
            sections.append(f"- Confidence: {pod.collective_confidence:.2f}")
            if pod.synthesized_output:
                sections.append(pod.synthesized_output)
            sections.append("")

        if state.cross_pod_conflicts:
            sections.append("## Cross-Pod Deconfliction")
            resolved = sum(1 for c in state.cross_pod_conflicts if c.resolved)
            sections.append(f"- Total Conflicts: {len(state.cross_pod_conflicts)}")
            sections.append(f"- Resolved: {resolved}")
            sections.append(f"- Deconfliction Passes: {state.deconfliction_passes}")

        sections.append("\n## Confidence Summary")
        sections.append(f"- Final Confidence: {state.final_confidence:.3f}")
        sections.append(f"- Threshold Met: {'Yes' if state.threshold_met else 'No'}")

        return "\n".join(sections)


def create_pod_orchestrator(config: Dict[str, Any] = None) -> PodOrchestrator:
    """Create and configure a PodOrchestrator instance."""
    return PodOrchestrator(config)
