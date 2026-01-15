"""
Advanced Tracing System

Enterprise-grade tracing with causal lineage.
Captures persona builds, layer execution, refinement,
and Truth Engine decisions as hash-chained audit bundles.
"""

import logging
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class TraceType(Enum):
    """Types of trace entries."""
    QUERY_INIT = "query_init"
    TIER_SELECTION = "tier_selection"
    COORDINATE_BUILD = "coordinate_build"
    PERSONA_SELECTION = "persona_selection"
    PERSONA_INPUT = "persona_input"
    PERSONA_OUTPUT = "persona_output"
    LAYER_START = "layer_start"
    LAYER_END = "layer_end"
    SUBWORKFLOW = "subworkflow"
    REFINEMENT_STEP = "refinement_step"
    REFINEMENT_CYCLE = "refinement_cycle"
    TRUTH_ENGINE = "truth_engine"
    GATE_CHECK = "gate_check"
    RELEASE_DECISION = "release_decision"
    MEMORY_PATCH = "memory_patch"


class TraceVisibility(Enum):
    """Visibility levels for tier-aware tracing."""
    PUBLIC = "public"      # User can see
    AUDIT = "audit"        # Auditors only
    INTERNAL = "internal"  # Engineering only


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class TraceEntry:
    """
    Single trace entry with hash linking.
    """
    trace_id: str = ""
    trace_type: TraceType = TraceType.QUERY_INIT
    timestamp: str = ""
    
    # Content
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Hash chain
    previous_hash: str = ""
    content_hash: str = ""
    
    # Visibility
    visibility: TraceVisibility = TraceVisibility.AUDIT
    tier_minimum: int = 1
    
    def __post_init__(self):
        if not self.trace_id:
            import uuid
            self.trace_id = f"tr_{uuid.uuid4().hex[:12]}"
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.content_hash:
            self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute content hash."""
        content = json.dumps({
            "type": self.trace_type.value,
            "data": self.data,
            "prev": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "trace_type": self.trace_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "content_hash": self.content_hash,
            "visibility": self.visibility.value,
            "tier_minimum": self.tier_minimum
        }


@dataclass
class LayerTrace:
    """Trace for a single layer execution."""
    layer: int
    started_at: str = ""
    ended_at: str = ""
    
    # Inputs/outputs
    input_state_hash: str = ""
    output_state_hash: str = ""
    
    # Changes
    operations: List[str] = field(default_factory=list)
    gains: List[str] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    issues_fixed: List[str] = field(default_factory=list)
    
    # Sub-workflows
    subworkflows: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "input_state_hash": self.input_state_hash,
            "output_state_hash": self.output_state_hash,
            "operations": self.operations,
            "gains": self.gains,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "subworkflows": self.subworkflows
        }


@dataclass
class PersonaTrace:
    """Trace for persona execution."""
    persona_id: str
    profile_id: str = ""
    
    # Inputs
    input_bundle: Dict[str, Any] = field(default_factory=dict)
    
    # Outputs
    claims: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Confidence
    confidence_vector: Dict[str, float] = field(default_factory=dict)
    
    # Veto
    veto_flag: bool = False
    veto_conditions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "profile_id": self.profile_id,
            "input_bundle": self.input_bundle,
            "claims": self.claims,
            "constraints": self.constraints,
            "risks": self.risks,
            "recommendations": self.recommendations,
            "confidence_vector": self.confidence_vector,
            "veto_flag": self.veto_flag,
            "veto_conditions": self.veto_conditions
        }


@dataclass
class RefinementTrace:
    """Trace for refinement workflow."""
    cycle: int = 1
    steps_run: List[int] = field(default_factory=list)
    
    # Changes per step
    step_traces: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # Confidence delta
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    
    # Issues
    issues_detected: List[str] = field(default_factory=list)
    issues_resolved: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "steps_run": self.steps_run,
            "step_traces": self.step_traces,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "issues_detected": self.issues_detected,
            "issues_resolved": self.issues_resolved
        }


@dataclass
class AuditBundle:
    """
    Complete sealed audit bundle for a query.
    """
    query_id: str = ""
    tier: int = 3
    
    # Coordinate
    coordinate_id: str = ""
    
    # Traces
    entries: List[TraceEntry] = field(default_factory=list)
    persona_traces: Dict[str, PersonaTrace] = field(default_factory=dict)
    layer_traces: Dict[int, LayerTrace] = field(default_factory=dict)
    refinement_traces: List[RefinementTrace] = field(default_factory=list)
    
    # Truth Engine
    truth_result: Dict[str, Any] = field(default_factory=dict)
    
    # Final
    release_authorized: bool = False
    final_answer_hash: str = ""
    
    # Sealing
    sealed: bool = False
    sealed_at: str = ""
    bundle_hash: str = ""
    
    def seal(self) -> str:
        """Seal the bundle and return hash."""
        if self.sealed:
            return self.bundle_hash
        
        self.sealed = True
        self.sealed_at = datetime.now(UTC).isoformat()
        
        # Compute bundle hash from all entries
        content = json.dumps({
            "query_id": self.query_id,
            "tier": self.tier,
            "entry_count": len(self.entries),
            "persona_count": len(self.persona_traces),
            "layer_count": len(self.layer_traces),
            "truth": self.truth_result.get("status", ""),
            "release": self.release_authorized
        }, sort_keys=True)
        
        self.bundle_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.bundle_hash
    
    def to_dict(self, include_full_traces: bool = False) -> Dict[str, Any]:
        """Serialize bundle."""
        result = {
            "query_id": self.query_id,
            "tier": self.tier,
            "coordinate_id": self.coordinate_id,
            "entry_count": len(self.entries),
            "personas": list(self.persona_traces.keys()),
            "layers_run": list(self.layer_traces.keys()),
            "refinement_cycles": len(self.refinement_traces),
            "truth_status": self.truth_result.get("status", "unknown"),
            "release_authorized": self.release_authorized,
            "sealed": self.sealed,
            "sealed_at": self.sealed_at,
            "bundle_hash": self.bundle_hash
        }
        
        if include_full_traces:
            result["entries"] = [e.to_dict() for e in self.entries]
            result["persona_traces"] = {k: v.to_dict() for k, v in self.persona_traces.items()}
            result["layer_traces"] = {k: v.to_dict() for k, v in self.layer_traces.items()}
            result["refinement_traces"] = [r.to_dict() for r in self.refinement_traces]
            result["truth_result"] = self.truth_result
        
        return result


# =============================================================================
# Tracing System
# =============================================================================

class TracingSystem:
    """
    Advanced Tracing System
    
    Captures complete causal lineage for UKG executions.
    Supports hash-chained entries and tier-aware visibility.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize tracing system."""
        self.config = config or {}
        self._bundles: Dict[str, AuditBundle] = {}
        self._current_bundle: Optional[AuditBundle] = None
        
        logger.info("TracingSystem initialized")
    
    def start_trace(self, query_id: str, tier: int) -> AuditBundle:
        """Start a new trace bundle for a query."""
        bundle = AuditBundle(query_id=query_id, tier=tier)
        self._bundles[query_id] = bundle
        self._current_bundle = bundle
        
        # Add init entry
        self._add_entry(TraceType.QUERY_INIT, {
            "query_id": query_id,
            "tier": tier
        })
        
        logger.info(f"Started trace for query {query_id}")
        return bundle
    
    def trace_tier_decision(self, decision: Dict[str, Any]) -> None:
        """Trace tier selection decision."""
        self._add_entry(TraceType.TIER_SELECTION, decision)
    
    def trace_coordinate(self, coordinate_id: str, axes: Dict[str, Any]) -> None:
        """Trace coordinate build."""
        if self._current_bundle:
            self._current_bundle.coordinate_id = coordinate_id
        
        self._add_entry(TraceType.COORDINATE_BUILD, {
            "coordinate_id": coordinate_id,
            "axes": axes
        })
    
    def trace_persona_selection(self, personas: List[str]) -> None:
        """Trace persona selection."""
        self._add_entry(TraceType.PERSONA_SELECTION, {
            "personas_selected": personas
        })
    
    def trace_persona_output(self, persona_trace: PersonaTrace) -> None:
        """Trace persona execution output."""
        if self._current_bundle:
            self._current_bundle.persona_traces[persona_trace.persona_id] = persona_trace
        
        self._add_entry(TraceType.PERSONA_OUTPUT, persona_trace.to_dict())
    
    def start_layer(self, layer: int, input_hash: str) -> LayerTrace:
        """Start layer trace."""
        trace = LayerTrace(
            layer=layer,
            started_at=datetime.now(UTC).isoformat(),
            input_state_hash=input_hash
        )
        
        if self._current_bundle:
            self._current_bundle.layer_traces[layer] = trace
        
        self._add_entry(TraceType.LAYER_START, {
            "layer": layer,
            "input_hash": input_hash
        })
        
        return trace
    
    def end_layer(self, layer: int, output_hash: str, gains: List[str]) -> None:
        """End layer trace."""
        if self._current_bundle and layer in self._current_bundle.layer_traces:
            trace = self._current_bundle.layer_traces[layer]
            trace.ended_at = datetime.now(UTC).isoformat()
            trace.output_state_hash = output_hash
            trace.gains = gains
        
        self._add_entry(TraceType.LAYER_END, {
            "layer": layer,
            "output_hash": output_hash,
            "gains": gains
        })
    
    def trace_subworkflow(
        self,
        layer: int,
        subworkflow: str,
        result: Dict[str, Any]
    ) -> None:
        """Trace sub-workflow execution."""
        if self._current_bundle and layer in self._current_bundle.layer_traces:
            self._current_bundle.layer_traces[layer].subworkflows.append({
                "name": subworkflow,
                "result": result
            })
        
        self._add_entry(TraceType.SUBWORKFLOW, {
            "layer": layer,
            "subworkflow": subworkflow,
            "result": result
        })
    
    def trace_refinement_step(
        self,
        step: int,
        name: str,
        issues: List[str],
        actions: List[str]
    ) -> None:
        """Trace single refinement step."""
        self._add_entry(TraceType.REFINEMENT_STEP, {
            "step": step,
            "name": name,
            "issues_detected": issues,
            "actions_taken": actions
        })
    
    def trace_refinement_cycle(self, refinement_trace: RefinementTrace) -> None:
        """Trace complete refinement cycle."""
        if self._current_bundle:
            self._current_bundle.refinement_traces.append(refinement_trace)
        
        self._add_entry(TraceType.REFINEMENT_CYCLE, refinement_trace.to_dict())
    
    def trace_truth_engine(self, result: Dict[str, Any]) -> None:
        """Trace Truth Engine evaluation."""
        if self._current_bundle:
            self._current_bundle.truth_result = result
            self._current_bundle.release_authorized = result.get("release_authorized", False)
        
        self._add_entry(TraceType.TRUTH_ENGINE, result)
    
    def seal_bundle(self, query_id: str, final_answer_hash: str = "") -> AuditBundle:
        """Seal and finalize the audit bundle."""
        bundle = self._bundles.get(query_id)
        if not bundle:
            raise ValueError(f"No bundle for query: {query_id}")
        
        bundle.final_answer_hash = final_answer_hash
        bundle.seal()
        
        logger.info(f"Sealed bundle {query_id}: {bundle.bundle_hash}")
        
        return bundle
    
    def get_bundle(self, query_id: str) -> Optional[AuditBundle]:
        """Get bundle by query ID."""
        return self._bundles.get(query_id)
    
    def _add_entry(self, trace_type: TraceType, data: Dict[str, Any]) -> TraceEntry:
        """Add entry to current bundle."""
        if not self._current_bundle:
            return None
        
        # Get previous hash
        prev_hash = ""
        if self._current_bundle.entries:
            prev_hash = self._current_bundle.entries[-1].content_hash
        
        entry = TraceEntry(
            trace_type=trace_type,
            data=data,
            previous_hash=prev_hash
        )
        
        self._current_bundle.entries.append(entry)
        return entry
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tracing metrics."""
        return {
            "total_bundles": len(self._bundles),
            "sealed_bundles": sum(1 for b in self._bundles.values() if b.sealed)
        }


# =============================================================================
# Factory
# =============================================================================

def create_tracing_system(config: Dict[str, Any] = None) -> TracingSystem:
    """Create tracing system instance."""
    return TracingSystem(config)
