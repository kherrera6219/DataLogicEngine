"""
Pod Orchestrator for Persona Scaling System

This module orchestrates the execution of expanded persona pods, including:
- Pod spawning based on expansion plans
- Within-pod synthesis (consolidating outputs from personas in the same pod)
- Cross-pod deconfliction (resolving conflicts between pods)
- Integration with the DRL loop for recursive refinement
"""

import uuid
import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from quad_persona.pod_models import (
    PodType,
    ExpandedPersona,
    PodState,
    CrossPodConflict,
    ScalingDecision,
    ExpansionPlan,
    ScalingOrchestrationState
)
from quad_persona.persona_scaling import (
    DEFENSE_SUBSYSTEM_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES,
    REGULATORY_PROFILES,
    COMPLIANCE_PROFILES
)


logger = logging.getLogger(__name__)


# =============================================================================
# Persona Builder
# =============================================================================

class PersonaBuilder:
    """
    Builds expanded personas based on subsystem profiles.
    
    Creates specialized personas with 7-part expert profiles filled from
    the subsystem profile templates.
    """
    
    # Profile registries by pod type
    PROFILE_REGISTRIES = {
        PodType.KNOWLEDGE: DEFENSE_SUBSYSTEM_PROFILES,
        PodType.SECTOR: SECTOR_SUBSYSTEM_PROFILES,
        PodType.REGULATORY: REGULATORY_PROFILES,
        PodType.COMPLIANCE: COMPLIANCE_PROFILES
    }
    
    @classmethod
    def build_persona(
        cls,
        pod_type: PodType,
        subsystem_id: str,
        context: Dict[str, Any] = None
    ) -> Optional[ExpandedPersona]:
        """
        Build an expanded persona for a specific subsystem.
        
        Args:
            pod_type: Type of pod (knowledge, sector, regulatory, compliance)
            subsystem_id: ID of the subsystem to specialize for (can be key or subsystem_id)
            context: Query context for customization
            
        Returns:
            ExpandedPersona or None if subsystem not found
        """
        registry = cls.PROFILE_REGISTRIES.get(pod_type, {})
        
        # First, try direct key lookup
        profile = registry.get(subsystem_id)
        
        # If not found, try matching by subsystem_id field
        if not profile:
            for key, prof in registry.items():
                if prof.subsystem_id == subsystem_id:
                    profile = prof
                    break
        
        # If still not found, try matching by removing _sme suffix
        if not profile and subsystem_id.endswith("_sme"):
            base_key = subsystem_id.replace("_sme", "")
            profile = registry.get(base_key)
        
        if not profile:
            logger.warning(f"Subsystem profile not found: {subsystem_id} for {pod_type.value}")
            return None
        
        # Create expanded persona from profile
        persona = ExpandedPersona(
            persona_id=f"{pod_type.value}_{subsystem_id}_{uuid.uuid4().hex[:8]}",
            pod_type=pod_type,
            name=profile.name,
            description=profile.specialization,
            subsystem_profile=profile
        )
        
        # Fill 7-part components from profile
        persona.set_component("job_role", profile.job_role)
        persona.set_component("education", profile.education)
        persona.set_component("certifications", {
            "items": profile.required_certifications,
            "standards": profile.related_standards
        })
        persona.set_component("skills", profile.skills)
        persona.set_component("training", {
            "domain": profile.domain,
            "specialization": profile.specialization
        })
        persona.set_component("career_path", profile.career_path)
        persona.set_component("related_jobs", profile.related_jobs)
        
        # Add context-specific metadata
        if context:
            persona.metadata["query_context"] = {
                "domain": context.get("domain"),
                "sector": context.get("sector"),
                "location": context.get("location")
            }
        
        logger.info(f"Built persona: {persona.name} ({persona.persona_id})")
        return persona
    
    @classmethod
    def build_default_persona(
        cls,
        pod_type: PodType,
        index: int,
        context: Dict[str, Any] = None
    ) -> ExpandedPersona:
        """
        Build a default expanded persona when no specific subsystem is detected.
        """
        default_names = {
            PodType.KNOWLEDGE: [
                "Domain Expert", "Technical SME", "Research Analyst",
                "Systems Analyst", "Architecture Expert", "Integration Specialist"
            ],
            PodType.SECTOR: [
                "Industry Analyst", "Operations Expert", "Program Analyst",
                "Business Analyst", "Strategy Consultant", "Implementation Lead"
            ],
            PodType.REGULATORY: [
                "Regulatory Analyst", "Policy Expert", "Compliance Advisor"
            ],
            PodType.COMPLIANCE: [
                "Compliance Officer", "Audit Specialist", "Standards Expert"
            ]
        }
        
        names = default_names.get(pod_type, ["Expert"])
        name = names[index % len(names)]
        
        persona = ExpandedPersona(
            persona_id=f"{pod_type.value}_default_{index}_{uuid.uuid4().hex[:8]}",
            pod_type=pod_type,
            name=name,
            description=f"Expert in {pod_type.value} domain"
        )
        
        # Fill with generic components
        persona.set_component("job_role", {"title": name, "level": "Senior"})
        persona.set_component("education", {"degree": "Advanced Degree"})
        persona.set_component("skills", {"items": [f"{pod_type.value} expertise"]})
        
        return persona


# =============================================================================
# Pod Synthesizer
# =============================================================================

class PodSynthesizer:
    """
    Synthesizes outputs from multiple personas within a single pod.
    
    Produces a consolidated output representing the pod's collective perspective.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the synthesizer."""
        self.config = config or {}
        self.synthesis_threshold = self.config.get("synthesis_threshold", 0.8)
    
    def synthesize(self, pod: PodState) -> Tuple[str, float]:
        """
        Synthesize outputs from all personas in a pod.
        
        Args:
            pod: PodState containing personas and their responses
            
        Returns:
            Tuple of (synthesized_output, collective_confidence)
        """
        if not pod.personas:
            return "", 0.0
        
        logger.info(f"Synthesizing {len(pod.personas)} personas in {pod.pod_type.value} pod")
        
        # Collect active persona responses
        active_personas = [p for p in pod.personas if p.is_active and p.response]
        
        if not active_personas:
            logger.warning(f"No active personas with responses in {pod.pod_type.value} pod")
            return "", 0.0
        
        # Detect internal conflicts
        conflicts = self._detect_internal_conflicts(active_personas)
        pod.internal_conflicts = conflicts
        
        # Build synthesized output
        sections = []
        
        # Header
        sections.append(f"## {pod.pod_type.value.title()} Pod Synthesis")
        sections.append(f"*Consolidated from {len(active_personas)} expert perspectives*\n")
        
        # Key findings section
        sections.append("### Key Findings")
        for persona in active_personas:
            sections.append(f"- **{persona.name}**: {persona.response[:200]}...")
        
        # Consensus section (if no major conflicts)
        if not any(c["severity"] in ("high", "critical") for c in conflicts):
            sections.append("\n### Pod Consensus")
            # In production, this would use LLM to generate consensus
            sections.append("The pod reached consensus on the key technical points.")
        else:
            sections.append("\n### Unresolved Items")
            for conflict in conflicts:
                sections.append(f"- {conflict['description']}")
        
        # Confidence summary
        average_confidence = sum(p.confidence for p in active_personas) / len(active_personas)
        sections.append(f"\n*Pod Confidence: {average_confidence:.2f}*")
        
        synthesized_output = "\n".join(sections)
        
        # Calculate collective confidence
        collective_confidence = pod.calculate_collective_confidence()
        
        pod.synthesized_output = synthesized_output
        
        return synthesized_output, collective_confidence
    
    def _detect_internal_conflicts(
        self,
        personas: List[ExpandedPersona]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between personas within the same pod."""
        conflicts = []
        
        for i, p1 in enumerate(personas):
            for p2 in personas[i+1:]:
                # Check for confidence divergence
                conf_diff = abs(p1.confidence - p2.confidence)
                
                if conf_diff > 0.3:
                    conflicts.append({
                        "type": "confidence_divergence",
                        "personas": [p1.persona_id, p2.persona_id],
                        "description": f"Confidence divergence between {p1.name} ({p1.confidence:.2f}) and {p2.name} ({p2.confidence:.2f})",
                        "severity": "medium" if conf_diff < 0.5 else "high"
                    })
        
        return conflicts


# =============================================================================
# Cross-Pod Deconfliction
# =============================================================================

class CrossPodDeconfliction:
    """
    Resolves conflicts between different pods.
    
    Regulatory/Compliance pods act as constraint checkers on Knowledge/Sector pods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize deconfliction."""
        self.config = config or {}
        self.max_iterations = self.config.get("max_deconfliction_iterations", 3)
    
    def deconflict(
        self,
        pods: Dict[str, PodState]
    ) -> Tuple[List[CrossPodConflict], bool]:
        """
        Perform cross-pod deconfliction.
        
        Args:
            pods: Dictionary of pod states by pod type
            
        Returns:
            Tuple of (conflicts_list, all_resolved)
        """
        logger.info("Starting cross-pod deconfliction")
        
        conflicts = []
        
        # Check Knowledge vs Regulatory constraints
        if PodType.KNOWLEDGE.value in pods and PodType.REGULATORY.value in pods:
            k_conflicts = self._check_constraint_violations(
                pods[PodType.KNOWLEDGE.value],
                pods[PodType.REGULATORY.value],
                "regulatory"
            )
            conflicts.extend(k_conflicts)
        
        # Check Sector vs Compliance constraints
        if PodType.SECTOR.value in pods and PodType.COMPLIANCE.value in pods:
            s_conflicts = self._check_constraint_violations(
                pods[PodType.SECTOR.value],
                pods[PodType.COMPLIANCE.value],
                "compliance"
            )
            conflicts.extend(s_conflicts)
        
        # Check Knowledge vs Sector alignment
        if PodType.KNOWLEDGE.value in pods and PodType.SECTOR.value in pods:
            alignment_conflicts = self._check_alignment(
                pods[PodType.KNOWLEDGE.value],
                pods[PodType.SECTOR.value]
            )
            conflicts.extend(alignment_conflicts)
        
        # Attempt automatic resolution
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
        constraint_type: str
    ) -> List[CrossPodConflict]:
        """Check if source pod violates constraints from constraint pod."""
        conflicts = []
        
        # In production, this would analyze actual outputs
        # For now, check confidence discrepancies as proxy
        source_conf = source_pod.collective_confidence
        constraint_conf = constraint_pod.collective_confidence
        
        if source_conf > 0.9 and constraint_conf < 0.7:
            conflicts.append(CrossPodConflict(
                source_pod=source_pod.pod_type,
                target_pod=constraint_pod.pod_type,
                conflict_type="constraint_uncertainty",
                source_claim=f"{source_pod.pod_type.value} outputs may not satisfy {constraint_type} constraints",
                target_claim=f"{constraint_pod.pod_type.value} has low confidence in constraint verification",
                severity="medium"
            ))
        
        return conflicts
    
    def _check_alignment(
        self,
        pod1: PodState,
        pod2: PodState
    ) -> List[CrossPodConflict]:
        """Check alignment between two pods."""
        conflicts = []
        
        # Check confidence alignment
        conf_diff = abs(pod1.collective_confidence - pod2.collective_confidence)
        
        if conf_diff > 0.25:
            conflicts.append(CrossPodConflict(
                source_pod=pod1.pod_type,
                target_pod=pod2.pod_type,
                conflict_type="alignment_gap",
                source_claim=f"{pod1.pod_type.value} confidence: {pod1.collective_confidence:.2f}",
                target_claim=f"{pod2.pod_type.value} confidence: {pod2.collective_confidence:.2f}",
                severity="low" if conf_diff < 0.35 else "medium"
            ))
        
        return conflicts
    
    def _try_resolve(
        self,
        conflict: CrossPodConflict,
        pods: Dict[str, PodState]
    ) -> bool:
        """Attempt to automatically resolve a conflict."""
        
        # Low severity conflicts can be resolved by accepting the more confident pod
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
        
        # Medium severity - flag for review but continue
        if conflict.severity == "medium":
            conflict.resolution = "Flagged for human review; proceeding with constraints applied"
            conflict.resolution_method = "constraint_priority"
            conflict.resolved = True
            return True
        
        # High/Critical - cannot auto-resolve
        return False


# =============================================================================
# Pod Orchestrator
# =============================================================================

class PodOrchestrator:
    """
    Main orchestrator for persona pod execution.
    
    Coordinates:
    1. Pod spawning based on expansion plans
    2. Parallel persona processing within pods
    3. Within-pod synthesis
    4. Cross-pod deconfliction
    5. Final integration
    """
    
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
        base_persona_results: Dict[str, Dict[str, Any]] = None
    ) -> ScalingOrchestrationState:
        """
        Execute full pod orchestration.
        
        Args:
            query: Original query text
            context: Query context
            scaling_decision: Decision from sufficiency tool
            base_persona_results: Results from base quad processing
            
        Returns:
            ScalingOrchestrationState with complete results
        """
        logger.info("Starting pod orchestration")
        
        # Initialize state
        state = ScalingOrchestrationState(
            query_id=context.get("query_id", str(uuid.uuid4())),
            query_text=query,
            scaling_decision=scaling_decision
        )
        
        state.update_status("processing", "pod_spawning")
        
        # If quad-only, return early with base results
        if not scaling_decision.should_expand:
            logger.info("Quad-only mode: Skipping pod expansion")
            state.update_status("completed", "quad_only")
            state.final_confidence = self._calculate_base_confidence(base_persona_results)
            state.threshold_met = state.final_confidence >= self.confidence_threshold
            return state
        
        try:
            # Phase 1: Spawn pods
            pods = self._spawn_pods(
                scaling_decision.expansion_plan,
                context
            )
            for pod in pods:
                state.add_pod(pod)
            
            state.update_status("processing", "persona_processing")
            
            # Phase 2: Process personas in parallel
            self._process_all_pods(state, query, context)
            
            state.update_status("processing", "within_pod_synthesis")
            
            # Phase 3: Within-pod synthesis
            for pod in state.pods.values():
                self.synthesizer.synthesize(pod)
                pod.update_status("completed")
            
            state.update_status("processing", "cross_pod_deconfliction")
            
            # Phase 4: Cross-pod deconfliction
            conflicts, all_resolved = self.deconfliction.deconflict(state.pods)
            state.cross_pod_conflicts = conflicts
            state.deconfliction_passes = 1
            
            # Retry deconfliction if needed
            while not all_resolved and state.deconfliction_passes < state.max_deconfliction_passes:
                state.deconfliction_passes += 1
                conflicts, all_resolved = self.deconfliction.deconflict(state.pods)
                state.cross_pod_conflicts = conflicts
            
            state.update_status("processing", "final_synthesis")
            
            # Phase 5: Final synthesis
            state.final_synthesis = self._create_final_synthesis(state)
            state.final_confidence = self._calculate_final_confidence(state)
            state.threshold_met = state.final_confidence >= self.confidence_threshold
            
            state.update_status("completed", "success")
            
        except Exception as e:
            logger.error(f"Pod orchestration failed: {e}")
            state.update_status("failed", str(e))
            raise
        
        return state
    
    def _spawn_pods(
        self,
        expansion_plan: ExpansionPlan,
        context: Dict[str, Any]
    ) -> List[PodState]:
        """Spawn pods based on expansion plan."""
        pods = []
        
        for pod_type in PodType:
            spawn_count = expansion_plan.spawn_counts.get(pod_type.value, 0)
            
            if spawn_count == 0:
                continue
            
            pod = PodState(pod_type=pod_type)
            
            # Get subsystems to spawn for this pod
            subsystems = expansion_plan.subsystems_to_spawn.get(pod_type.value, [])
            
            # Build personas from subsystems
            for i, subsystem_id in enumerate(subsystems[:spawn_count]):
                persona = PersonaBuilder.build_persona(pod_type, subsystem_id, context)
                if persona:
                    pod.add_persona(persona)
            
            # Fill remaining slots with default personas
            while pod.persona_count < spawn_count:
                default_persona = PersonaBuilder.build_default_persona(
                    pod_type,
                    pod.persona_count,
                    context
                )
                pod.add_persona(default_persona)
            
            pods.append(pod)
            logger.info(f"Spawned {pod_type.value} pod with {pod.persona_count} personas")
        
        return pods
    
    def _process_all_pods(
        self,
        state: ScalingOrchestrationState,
        query: str,
        context: Dict[str, Any]
    ):
        """Process all personas across all pods."""
        
        # Collect all personas
        all_tasks = []
        for pod in state.pods.values():
            for persona in pod.personas:
                all_tasks.append((pod, persona, query, context))
        
        # Process in parallel
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
        task: Tuple[PodState, ExpandedPersona, str, Dict[str, Any]]
    ) -> Tuple[str, float]:
        """Process a single persona's response."""
        pod, persona, query, context = task
        
        start_time = datetime.now(UTC)
        
        # In production, this would call the LLM with persona context
        # For now, generate simulated response
        response = self._generate_persona_response(persona, query, context)
        confidence = self._calculate_persona_confidence(persona, query, context)
        
        end_time = datetime.now(UTC)
        persona.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return response, confidence
    
    def _generate_persona_response(
        self,
        persona: ExpandedPersona,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate response for a persona (simulated for now)."""
        return f"[{persona.name}] Analysis of: {query[:100]}... " \
               f"Based on expertise in {persona.description}."
    
    def _calculate_persona_confidence(
        self,
        persona: ExpandedPersona,
        query: str,
        context: Dict[str, Any]
    ) -> float:
        """Calculate confidence for persona response."""
        # Base confidence from persona type
        base_confidence = {
            PodType.KNOWLEDGE: 0.85,
            PodType.SECTOR: 0.82,
            PodType.REGULATORY: 0.88,
            PodType.COMPLIANCE: 0.86
        }.get(persona.pod_type, 0.80)
        
        # Adjust for subsystem specificity
        if persona.subsystem_profile:
            # More specific = higher confidence
            base_confidence += 0.05
        
        # Add small random variation
        import random
        variation = random.uniform(-0.05, 0.05)
        
        return min(0.99, max(0.5, base_confidence + variation))
    
    def _calculate_base_confidence(
        self,
        base_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate confidence from base quad results."""
        if not base_results:
            return 0.5
        
        confidences = [r.get("confidence", 0.5) for r in base_results.values()]
        return sum(confidences) / len(confidences)
    
    def _calculate_final_confidence(
        self,
        state: ScalingOrchestrationState
    ) -> float:
        """Calculate final confidence from orchestration state."""
        if not state.pods:
            return 0.5
        
        # Weight pods by type
        weights = {
            PodType.KNOWLEDGE.value: 0.30,
            PodType.SECTOR.value: 0.25,
            PodType.REGULATORY.value: 0.25,
            PodType.COMPLIANCE.value: 0.20
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for pod_type, pod in state.pods.items():
            weight = weights.get(pod_type, 0.25)
            weighted_sum += pod.collective_confidence * weight
            total_weight += weight
        
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Penalize for unresolved conflicts
        unresolved = sum(1 for c in state.cross_pod_conflicts if not c.resolved)
        penalty = unresolved * 0.02
        
        return max(0.5, base_confidence - penalty)
    
    def _create_final_synthesis(
        self,
        state: ScalingOrchestrationState
    ) -> str:
        """Create final synthesized output from all pods."""
        sections = []
        
        sections.append("# Expanded Committee Response")
        sections.append(f"*Query: {state.query_text[:100]}...*\n")
        
        # Add pod summaries
        for pod_type, pod in state.pods.items():
            sections.append(f"## {pod_type.title()} Expert Pod")
            sections.append(f"- Personas: {pod.persona_count}")
            sections.append(f"- Confidence: {pod.collective_confidence:.2f}")
            if pod.synthesized_output:
                sections.append(pod.synthesized_output)
            sections.append("")
        
        # Conflict summary
        if state.cross_pod_conflicts:
            sections.append("## Cross-Pod Deconfliction")
            resolved = sum(1 for c in state.cross_pod_conflicts if c.resolved)
            sections.append(f"- Total Conflicts: {len(state.cross_pod_conflicts)}")
            sections.append(f"- Resolved: {resolved}")
            sections.append(f"- Deconfliction Passes: {state.deconfliction_passes}")
        
        # Final metrics
        sections.append("\n## Confidence Summary")
        sections.append(f"- Final Confidence: {state.final_confidence:.3f}")
        sections.append(f"- Threshold Met: {'Yes' if state.threshold_met else 'No'}")
        
        return "\n".join(sections)


# =============================================================================
# Factory Function
# =============================================================================

def create_pod_orchestrator(config: Dict[str, Any] = None) -> PodOrchestrator:
    """Create and configure a PodOrchestrator instance."""
    return PodOrchestrator(config)
