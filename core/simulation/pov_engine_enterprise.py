"""
Enterprise POV Engine

Enterprise-grade wrapper for the POV Engine that integrates:
- POV Policy Service (mode selection, viewpoint roster)
- Viewpoint Registry (governed catalog)
- Delta Normalizer (structured output)
- Persona Scaling System (KA-21 integration)
- Budget controls and telemetry

This module provides the POVEngineEnterprise class which wraps the base
POVEngine with enterprise features while maintaining backward compatibility.
"""

import logging
import time
import uuid
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Any, Optional

# Base POV Engine
from core.simulation.pov_engine import POVEngine

# Enterprise components
from core.simulation.pov_policy import (
    POVPolicyService,
    POVPlan,
    POVMode,
    POVBudget
)
from core.simulation.viewpoint_registry import (
    ViewpointRegistry,
    ViewpointProfile
)
from core.simulation.pov_delta import (
    POVDeltaNormalizer,
    POVDeltaCollection,
    POVDelta,
    POVResponse,
    POVRecommendations,
    POVTelemetry,
    DeltaType,
    Severity,
    Lane
)

# Persona Scaling integration (lazy import to avoid circular deps)
try:
    from core.persona.quad.persona_scaling import PersonaSufficiencyTool
    from core.persona.quad.pod_orchestrator import PodOrchestrator
    PERSONA_SCALING_AVAILABLE = True
except ImportError:
    PERSONA_SCALING_AVAILABLE = False


logger = logging.getLogger(__name__)


# =============================================================================
# Enterprise POV Request/Response
# =============================================================================

class POVRequest:
    """
    Enterprise POV Engine request.
    
    Structured input format with all required context.
    """
    
    def __init__(
        self,
        query_id: str,
        query_text: str,
        coordinate_context: Dict[str, Any] = None,
        working_subgraph_ref: str = None,
        quad_outputs: Dict[str, Any] = None,
        budget: POVBudget = None,
        policy_mode: str = "standard"
    ):
        self.query_id = query_id
        self.query_text = query_text
        self.coordinate_context = coordinate_context or {}
        self.working_subgraph_ref = working_subgraph_ref
        self.quad_outputs = quad_outputs or {}
        self.budget = budget or POVBudget()
        self.policy_mode = policy_mode
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POVRequest":
        """Create from dictionary."""
        budget = None
        if "budget" in data:
            budget = POVBudget.from_dict(data["budget"])
        
        return cls(
            query_id=data.get("query_id", str(uuid.uuid4())),
            query_text=data.get("query_text", ""),
            coordinate_context=data.get("coordinate_context", {}),
            working_subgraph_ref=data.get("working_subgraph_ref"),
            quad_outputs=data.get("quad_outputs", {}),
            budget=budget,
            policy_mode=data.get("policy_mode", "standard")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "coordinate_context": self.coordinate_context,
            "working_subgraph_ref": self.working_subgraph_ref,
            "quad_outputs": self.quad_outputs,
            "budget": self.budget.to_dict(),
            "policy_mode": self.policy_mode
        }


# =============================================================================
# Enterprise POV Engine
# =============================================================================

class POVEngineEnterprise:
    """
    Enterprise-grade POV Engine.
    
    Integrates all enterprise components:
    - Policy Service for mode selection
    - Viewpoint Registry for governed profiles
    - Delta Normalizer for structured output
    - Persona Scaling for committee mode
    - Budget controls and circuit breakers
    - Telemetry and observability
    """
    
    def __init__(self, config: Dict[str, Any] = None, system_manager=None):
        """
        Initialize the Enterprise POV Engine.
        
        Args:
            config: Configuration dictionary
            system_manager: Optional system manager reference
        """
        self.config = config or {}
        self.system_manager = system_manager
        
        # Initialize enterprise components
        self.policy_service = POVPolicyService(self.config.get("policy", {}))
        self.viewpoint_registry = ViewpointRegistry(self.config.get("registry", {}))
        self.delta_normalizer = POVDeltaNormalizer(self.config.get("normalizer", {}))
        
        # Initialize base POV Engine for core expansion logic
        self.base_engine = POVEngine(
            config=self.config.get("base_engine", {}),
            system_manager=system_manager
        )
        
        # Initialize persona scaling if available
        self.persona_scaling_tool = None
        self.pod_orchestrator = None
        if PERSONA_SCALING_AVAILABLE:
            self.persona_scaling_tool = PersonaSufficiencyTool(
                self.config.get("persona_scaling", {})
            )
            self.pod_orchestrator = PodOrchestrator(
                self.config.get("pod_orchestrator", {})
            )
        
        # Runtime controls
        self.max_parallel = self.config.get("max_parallel_viewpoints", 4)
        self.default_viewpoint_timeout = self.config.get("viewpoint_timeout_ms", 2000)
        self.circuit_breaker_threshold = self.config.get("circuit_breaker_failures", 3)
        
        # State tracking
        self._failed_viewpoints: Dict[str, int] = {}
        
        # Metrics
        self._total_requests = 0
        self._total_deltas = 0
        self._mode_counts = {m.value: 0 for m in POVMode}
        
        logger.info("POVEngineEnterprise initialized")
    
    def process(
        self,
        request: POVRequest
    ) -> POVResponse:
        """
        Process a POV request with full enterprise features.
        
        Args:
            request: POVRequest with all context
            
        Returns:
            POVResponse with structured deltas and telemetry
        """
        start_time = time.time()
        self._total_requests += 1
        
        # Initialize telemetry
        telemetry = POVTelemetry(
            start_time=datetime.now(UTC).isoformat()
        )
        
        logger.info(f"Processing POV request: {request.query_id}")
        
        try:
            # Step 1: Evaluate policy and get execution plan
            plan = self.policy_service.evaluate(
                query=request.query_text,
                context=request.coordinate_context,
                quad_outputs=request.quad_outputs,
                budget=request.budget,
                policy_mode=request.policy_mode
            )
            
            self._mode_counts[plan.mode.value] += 1
            telemetry.viewpoints_requested = plan.total_viewpoints
            
            # Step 2: Handle bypass mode
            if plan.mode == POVMode.BYPASS:
                logger.info("POV bypass mode - returning minimal response")
                return self._create_bypass_response(request, plan, telemetry, start_time)
            
            # Step 3: Execute base POV expansion
            base_context = self._prepare_context(request)
            expanded_context = self.base_engine.expand_context(
                query=request.query_text,
                initial_context=base_context
            )
            
            # Step 4: Execute selected viewpoints
            viewpoint_outputs = self._execute_viewpoints(
                plan=plan,
                expanded_context=expanded_context,
                budget=request.budget,
                telemetry=telemetry
            )
            
            # Step 5: Handle committee mode with persona scaling
            scaling_deltas = None
            if plan.mode == POVMode.COMMITTEE and self.pod_orchestrator:
                scaling_deltas = self._execute_persona_scaling(
                    request=request,
                    plan=plan,
                    expanded_context=expanded_context
                )
            
            # Step 6: Normalize all outputs to structured deltas
            working_subgraph = expanded_context.get("expanded_data", [])
            delta_collection = self.delta_normalizer.normalize(
                viewpoint_outputs=viewpoint_outputs,
                working_subgraph={"nodes": working_subgraph}
            )
            
            # Merge persona scaling deltas if present
            if scaling_deltas:
                for delta in scaling_deltas:
                    delta_collection.add_delta(delta)
            
            self._total_deltas += delta_collection.total_count
            telemetry.deltas_generated = delta_collection.total_count
            
            # Step 7: Build evidence bindings
            evidence_bindings = self._build_evidence_bindings(delta_collection)
            telemetry.evidence_bindings = len(evidence_bindings)
            
            # Step 8: Generate recommendations
            recommendations = self._generate_recommendations(
                delta_collection=delta_collection,
                plan=plan,
                expanded_context=expanded_context
            )
            
            # Step 9: Calculate confidence
            confidence = self._calculate_confidence(
                delta_collection=delta_collection,
                expanded_context=expanded_context
            )
            
            # Finalize telemetry
            telemetry.end_time = datetime.now(UTC).isoformat()
            telemetry.latency_ms = int((time.time() - start_time) * 1000)
            telemetry.recursions = expanded_context.get("pov_stats", {}).get("passes", 1)
            
            # Build response
            response = POVResponse(
                query_id=request.query_id,
                selected_viewpoints=[v.viewpoint_id for v in plan.viewpoints],
                pov_deltas=delta_collection,
                evidence_bindings=evidence_bindings,
                recommendations=recommendations,
                telemetry=telemetry,
                confidence=confidence
            )
            
            logger.info(f"POV complete: {delta_collection.total_count} deltas, "
                       f"{telemetry.latency_ms}ms, confidence={confidence:.3f}")
            
            return response
            
        except Exception as e:
            logger.error(f"POV processing failed: {e}")
            telemetry.end_time = datetime.now(UTC).isoformat()
            telemetry.latency_ms = int((time.time() - start_time) * 1000)
            
            # Return error response
            return POVResponse(
                query_id=request.query_id,
                telemetry=telemetry,
                confidence=0.0
            )
    
    def process_dict(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a POV request from dictionary format.
        
        Convenience method for API integration.
        """
        request = POVRequest.from_dict(request_data)
        response = self.process(request)
        return response.to_dict()
    
    # ===== Internal Methods =====
    
    def _prepare_context(self, request: POVRequest) -> Dict[str, Any]:
        """Prepare context for base POV engine."""
        return {
            "query": request.query_text,
            "query_id": request.query_id,
            "coordinate_context": request.coordinate_context,
            "axis_vector": request.coordinate_context.get("axis_vector", {}),
            "initial_data": [],
            **request.coordinate_context
        }
    
    def _create_bypass_response(
        self,
        request: POVRequest,
        plan: POVPlan,
        telemetry: POVTelemetry,
        start_time: float
    ) -> POVResponse:
        """Create minimal response for bypass mode."""
        telemetry.end_time = datetime.now(UTC).isoformat()
        telemetry.latency_ms = int((time.time() - start_time) * 1000)
        telemetry.viewpoints_run = 0
        
        return POVResponse(
            query_id=request.query_id,
            selected_viewpoints=[],
            pov_deltas=POVDeltaCollection(),
            recommendations=POVRecommendations(),
            telemetry=telemetry,
            confidence=0.95  # High confidence for simple queries
        )
    
    def _execute_viewpoints(
        self,
        plan: POVPlan,
        expanded_context: Dict[str, Any],
        budget: POVBudget,
        telemetry: POVTelemetry
    ) -> List[Dict[str, Any]]:
        """Execute selected viewpoints with budget controls."""
        outputs = []
        
        # Get profile details for selected viewpoints
        viewpoints_to_run = []
        for selection in plan.viewpoints:
            profile = self.viewpoint_registry.get_profile(selection.viewpoint_id)
            if profile:
                viewpoints_to_run.append((selection, profile))
            else:
                # Create from selection if not in registry
                viewpoints_to_run.append((selection, None))
        
        # Execute in parallel with timeout
        with ThreadPoolExecutor(max_workers=min(self.max_parallel, len(viewpoints_to_run))) as executor:
            futures = {}
            
            for selection, profile in viewpoints_to_run:
                # Check circuit breaker
                if self._is_circuit_open(selection.viewpoint_id):
                    telemetry.viewpoints_failed += 1
                    continue
                
                # Submit viewpoint execution
                timeout_ms = selection.timeout_ms or self.default_viewpoint_timeout
                future = executor.submit(
                    self._execute_single_viewpoint,
                    selection,
                    profile,
                    expanded_context
                )
                futures[future] = (selection, timeout_ms)
            
            # Collect results with timeout handling
            for future, (selection, timeout_ms) in futures.items():
                try:
                    result = future.result(timeout=timeout_ms / 1000.0)
                    if result:
                        outputs.append(result)
                        telemetry.viewpoints_run += 1
                except FuturesTimeoutError:
                    logger.warning(f"Viewpoint timeout: {selection.viewpoint_id}")
                    self._record_failure(selection.viewpoint_id)
                    telemetry.viewpoints_failed += 1
                except Exception as e:
                    logger.error(f"Viewpoint failed: {selection.viewpoint_id}: {e}")
                    self._record_failure(selection.viewpoint_id)
                    telemetry.viewpoints_failed += 1
        
        return outputs
    
    def _execute_single_viewpoint(
        self,
        selection,
        profile: Optional[ViewpointProfile],
        expanded_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single viewpoint."""
        # In production, this would call an LLM with the viewpoint profile
        # For now, generate simulated output based on profile
        
        viewpoint_id = selection.viewpoint_id
        lane = selection.lane
        
        # Get perspective from base engine personas if available
        personas = expanded_context.get("simulated_personas", [])
        matching_persona = None
        for persona in personas:
            if lane in persona.get("name", "").lower():
                matching_persona = persona
                break
        
        output = {
            "viewpoint_id": viewpoint_id,
            "name": profile.name if profile else selection.name,
            "lane": lane,
            "perspective": matching_persona.get("perspective", {}) if matching_persona else {},
            "confidence": 0.8 + (0.1 * (1 if profile else 0)),
            "findings": []
        }
        
        # Generate findings based on lane
        if lane == "regulatory":
            output["findings"].append({
                "type": "constraint",
                "severity": "high",
                "description": f"Regulatory review required for {viewpoint_id}",
                "owner_lane": "regulatory",
                "confidence": 0.85
            })
        elif lane == "compliance":
            output["findings"].append({
                "type": "requirement",
                "severity": "medium",
                "description": f"Compliance verification needed per {viewpoint_id}",
                "owner_lane": "compliance",
                "confidence": 0.80
            })
        elif lane == "stakeholder":
            output["findings"].append({
                "type": "recommendation",
                "severity": "medium",
                "description": f"Stakeholder consideration from {viewpoint_id}",
                "owner_lane": "sector",
                "confidence": 0.75
            })
        
        return output
    
    def _execute_persona_scaling(
        self,
        request: POVRequest,
        plan: POVPlan,
        expanded_context: Dict[str, Any]
    ) -> List[POVDelta]:
        """Execute persona scaling for committee mode."""
        if not self.persona_scaling_tool or not self.pod_orchestrator:
            return []
        
        deltas = []
        
        try:
            # Get axis vector
            axis_vector = request.coordinate_context.get("axis_vector", {})
            
            # Evaluate persona sufficiency
            scaling_decision = self.persona_scaling_tool.evaluate(
                query=request.query_text,
                context=request.coordinate_context,
                axis_vector=axis_vector,
                persona_results=request.quad_outputs
            )
            
            if scaling_decision.should_expand:
                # Run pod orchestration
                state = self.pod_orchestrator.orchestrate(
                    query=request.query_text,
                    context=request.coordinate_context,
                    scaling_decision=scaling_decision,
                    base_persona_results=request.quad_outputs
                )
                
                # Convert pod outputs to deltas
                for pod_type, pod in state.pods.items():
                    if pod.internal_conflicts:
                        for conflict in pod.internal_conflicts:
                            delta = POVDelta(
                                delta_type=DeltaType.RISK,
                                severity=Severity(conflict.get("severity", "medium")),
                                owner_lane=Lane(pod_type),
                                description=conflict.get("description", ""),
                                source_viewpoint=f"pod_{pod_type}",
                                source_lane=pod_type
                            )
                            deltas.append(delta)
                
                # Add cross-pod conflicts
                for conflict in state.cross_pod_conflicts:
                    if not conflict.resolved:
                        delta = POVDelta(
                            delta_type=DeltaType.RISK,
                            severity=Severity.HIGH,
                            owner_lane=Lane.CROSS_CUTTING,
                            description=f"Cross-pod conflict: {conflict.source_claim} vs {conflict.target_claim}",
                            source_viewpoint="pod_orchestrator",
                            source_lane="cross_cutting"
                        )
                        deltas.append(delta)
                        
        except Exception as e:
            logger.error(f"Persona scaling failed: {e}")
        
        return deltas
    
    def _build_evidence_bindings(
        self,
        delta_collection: POVDeltaCollection
    ) -> Dict[str, List[str]]:
        """Build evidence bindings map."""
        bindings = {}
        
        for delta in delta_collection._all_deltas():
            if delta.evidence_refs:
                key = f"{delta.delta_type.value}:{delta.delta_id}"
                bindings[key] = [e.uri for e in delta.evidence_refs]
        
        return bindings
    
    def _generate_recommendations(
        self,
        delta_collection: POVDeltaCollection,
        plan: POVPlan,
        expanded_context: Dict[str, Any]
    ) -> POVRecommendations:
        """Generate recommendations based on findings."""
        recommendations = POVRecommendations()
        
        # Check if more retrieval is needed
        gaps = delta_collection.gaps
        if len(gaps) > 2:
            recommendations.needs_more_retrieval = True
            recommendations.retrieval_hints = [
                g.description[:100] for g in gaps[:3]
            ]
        
        # Check if recursion is needed
        critical_unresolved = [
            d for d in delta_collection._all_deltas()
            if d.severity in (Severity.CRITICAL, Severity.HIGH) and not d.resolved
        ]
        if len(critical_unresolved) > 3:
            recommendations.needs_recursion = True
            recommendations.recursion_reason = f"{len(critical_unresolved)} critical/high items unresolved"
        
        # Suggest additional viewpoints
        if plan.mode == POVMode.STANDARD and delta_collection.critical_count > 0:
            recommendations.suggested_viewpoints = ["safety_advocate", "decision_maker"]
        
        return recommendations
    
    def _calculate_confidence(
        self,
        delta_collection: POVDeltaCollection,
        expanded_context: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence."""
        # Start with base POV confidence
        base_confidence = expanded_context.get("pov_confidence", 0.8)
        
        # Penalize for unresolved critical items
        critical = delta_collection.critical_count
        if critical > 0:
            base_confidence -= 0.05 * critical
        
        # Penalize for gaps
        gap_count = len(delta_collection.gaps)
        if gap_count > 0:
            base_confidence -= 0.02 * gap_count
        
        return max(0.5, min(0.99, base_confidence))
    
    def _is_circuit_open(self, viewpoint_id: str) -> bool:
        """Check if circuit breaker is open for a viewpoint."""
        failures = self._failed_viewpoints.get(viewpoint_id, 0)
        return failures >= self.circuit_breaker_threshold
    
    def _record_failure(self, viewpoint_id: str):
        """Record a viewpoint failure."""
        self._failed_viewpoints[viewpoint_id] = self._failed_viewpoints.get(viewpoint_id, 0) + 1
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers."""
        self._failed_viewpoints.clear()
    
    # ===== Metrics =====
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            "total_requests": self._total_requests,
            "total_deltas": self._total_deltas,
            "mode_counts": self._mode_counts,
            "circuit_breaker_states": {
                k: v >= self.circuit_breaker_threshold
                for k, v in self._failed_viewpoints.items()
            }
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_enterprise_pov_engine(
    config: Dict[str, Any] = None,
    system_manager=None
) -> POVEngineEnterprise:
    """Create and configure an Enterprise POV Engine instance."""
    return POVEngineEnterprise(config, system_manager)
