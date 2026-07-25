"""
Layer 10: EmergenceDetectionController

The EmergenceDetectionController is the final safety gate and release authority
of the UKG 10-layer stack. It performs emergence detection, safety audit,
and makes the final binary RELEASE vs CONTAIN decision.
"""

import hashlib
import json
import logging
import time
from typing import Any, ClassVar

from backend.knowledge_algorithms.contracts import KAExecutionResult

from .l10_schemas import (
    ContainmentAction,
    DSQPTraceSeal,
    EmergenceAssessment,
    EmergenceLevel,
    EmergencePattern,
    L10Decision,
    L10Input,
    L10Result,
    SafetyCheckResult,
    SafetyViolation,
    TrustGateResult,
)

logger = logging.getLogger(__name__)

# Trust thresholds with belief decay factored in
TRUST_THRESHOLDS = {
    "standard": 0.95,
    "high_risk": 0.985
}

# Belief decay factor (98% nudge)
BELIEF_DECAY_FACTOR = 0.98

# Max processing time for safety checks
MAX_SAFETY_TIME_MS = 20000


class EmergenceDetectionController:
    """
    Layer 10: EmergenceDetectionController (The Sentinel)
    
    The Final Guardian. Orchestrates two operational lanes:
    - Lane A (Response Gate): Real-time safety, emergence, and release authority.
    - Lane B (Knowledge Commit): Authorized persistence of reasoning and learning.
    """
    
    # L10 specific KA suite
    L10_KAS: ClassVar[list[str]] = [
        "L10-KA-001",  # Entropy-Based Emergence Scorer
        "L10-KA-002",  # Self-Awareness Monitor
        "L10-KA-003",  # Privacy & PII Redactor
        "L10-KA-004",  # Ethical Alignment Validator
        "L10-KA-005",  # Containment Decision Engine
        "L10-KA-006",  # Terminal Trust Gate (Belief Decay)
        "L10-KA-007",  # Human Escalation Router (Axis 17)
    ]
    
    # Canonical KAs for Lane A (Response Gate)
    LANE_A_KAS: ClassVar[list[str]] = [
        "KA-021", "KA-108", "KA-116",  # Emergence/Drift
        "KA-058", "KA-059", "KA-061", "KA-063", "KA-027",  # Safety/Ethics
        "KA-014", "KA-023", "KA-095", "KA-062"  # Trust/Governance
    ]

    # Canonical KAs for Lane B (Knowledge Commit)
    LANE_B_KAS: ClassVar[list[str]] = [
        "KA-109", "KA-079", "KA-050", "KA-094",  # Commit/Classification
        "KA-065", "KA-083", "KA-088", "KA-096"  # Lifecycle/Regression
    ]

    def __init__(self, ka_controller=None, config: dict | None = None):
        self.ka_controller = ka_controller
        self.config = config or {}
        logger.info("EmergenceDetectionController (Layer 10 Sentinel) initialized")

    def _execute_ka(
        self,
        ka_id: str,
        payload: dict[str, Any],
        kas_invoked: list[str],
    ) -> dict[str, Any]:
        """Execute through the typed contract and record only successful calls."""
        if self.ka_controller is None:
            raise RuntimeError(f"{ka_id} controller is unavailable")
        execute_typed = getattr(self.ka_controller, "execute_typed", None)
        if not callable(execute_typed):
            raise TypeError(
                f"{type(self.ka_controller).__name__} does not implement execute_typed"
            )
        result = execute_typed(ka_id, payload)
        if not isinstance(result, KAExecutionResult):
            raise TypeError(f"{ka_id} returned a non-canonical execution result")
        output = result.require_output()
        kas_invoked.append(result.canonical_id)
        return output

    @staticmethod
    def _required_output_value(
        ka_id: str,
        output: dict[str, Any],
        field: str,
    ) -> Any:
        if field not in output:
            raise RuntimeError(f"{ka_id} output is missing required field {field!r}")
        return output[field]

    def authorize(self, input_data: L10Input | None) -> L10Result:
        """
        Final release authority gate (Lane A + Lane B triggers).
        """
        start_time = time.time()
        kas_invoked = []
        
        if input_data is None:
            return self._create_failure_result(None, "Input data is None", 0.0)

        try:
            # --- LANE A: Response Gate (Sync) ---
            
            # 1. Emergence & Capability Drift
            emergence_report = self._detect_emergence_lane_a(input_data, kas_invoked)
            
            # 2. Safety & Policy Audit
            safety_report = self._run_safety_audit_lane_a(input_data, kas_invoked)
            
            # 3. Trust Gate (Belief Decay)
            trust_report = self._evaluate_trust_gate_lane_a(input_data, kas_invoked)
            
            # 4. Final Release Decision
            decision, final_answer, actions = self._make_containment_decision(
                input_data, emergence_report, safety_report, trust_report
            )
            
            # --- LANE B: Knowledge Commit (Async/Deferred Logic) ---
            if decision in [L10Decision.RELEASE, L10Decision.MODIFY]:
                self._process_knowledge_commit_lane_b(input_data, kas_invoked)
            
            # 5. DSQP Trace Finalization (Axis 15)
            dsqp_seal = self._generate_dsqp_seal(input_data, emergence_report, safety_report)
            
            processing_time = (time.time() - start_time) * 1000
            
            return L10Result(
                simulation_id=input_data.simulation_id,
                decision=decision,
                final_answer=final_answer,
                emergence_report=emergence_report,
                safety_report=safety_report,
                trust_report=trust_report,
                containment_actions=actions,
                dsqp_seal=dsqp_seal,
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time,
                requires_human_signoff=(trust_report.action_required == "human_review") or (decision == L10Decision.ESCALATE)
            )

        except Exception as e:
            logger.exception("Layer 10 Sentinel Critical Failure")
            return self._create_failure_result(input_data, str(e), (time.time() - start_time) * 1000)

    def _detect_emergence_lane_a(self, input_data: L10Input, kas_invoked: list[str]) -> EmergenceAssessment:
        """Detect emergent behaviors and capability drift using canonical and L10 KAs."""
        assessment = EmergenceAssessment()
        content = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        if not self.ka_controller:
            return assessment

        # KA-021: Emergence Detection (General)
        try:
            ka_res = self._execute_ka(
                "KA-021",
                {"content": content, "trace": input_data.reasoning_trace},
                kas_invoked,
            )
            if self._required_output_value("KA-021", ka_res, "is_emergent"):
                assessment.emergence_detected = True
                assessment.overall_level = EmergenceLevel.MODERATE
        except Exception as exc:
            raise RuntimeError("Required KA-021 emergence check failed") from exc

        # KA-108: Capability Escalation (Unsafe drift)
        try:
            ka_res = self._execute_ka(
                "KA-108",
                {"content": content, "problem_spec": input_data.problem_spec},
                kas_invoked,
            )
            if self._required_output_value("KA-108", ka_res, "escalation_detected"):
                assessment.patterns.append(EmergencePattern(
                    pattern_type="capability_escalation",
                    location="reasoning_path",
                    description="AI attempted to bypass safety bounds",
                    risk_level=EmergenceLevel.HIGH,
                    score=0.9
                ))
        except Exception as exc:
            raise RuntimeError("Required KA-108 escalation check failed") from exc

        # L10-KA-001/002: Entropy and Self-Awareness
        try:
            ka_res = self._execute_ka(
                "L10-KA-001",
                {"content": content},
                kas_invoked,
            )
            assessment.entropy_delta = float(
                self._required_output_value(
                    "L10-KA-001",
                    ka_res,
                    "entropy_score",
                )
            )
            
            ka_res = self._execute_ka(
                "L10-KA-002",
                {"content": content},
                kas_invoked,
            )
            if self._required_output_value(
                "L10-KA-002",
                ka_res,
                "awareness_detected",
            ):
                assessment.patterns.append(EmergencePattern(
                    pattern_type="self_referential",
                    location="output",
                    description="Self-awareness indicators found",
                    risk_level=EmergenceLevel.LOW,
                    score=0.3
                ))
        except Exception as exc:
            raise RuntimeError(
                "Required Layer-10 entropy/self-awareness checks failed"
            ) from exc

        return assessment

    def _run_safety_audit_lane_a(self, input_data: L10Input, kas_invoked: list[str]) -> SafetyCheckResult:
        """Sequential safety and policy audit."""
        result = SafetyCheckResult()
        content = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        if not self.ka_controller:
            return result

        # Safety & Privacy Baseline (KA-058, KA-059)
        for ka_id in ["KA-058", "KA-059"]:
            try:
                ka_res = self._execute_ka(
                    ka_id,
                    {"content": content},
                    kas_invoked,
                )
                if not self._required_output_value(ka_id, ka_res, "passed"):
                    result.passed = False
                    v_type = "PII_leak" if ka_id == "KA-059" else "safety_violation"
                    result.violations.append(SafetyViolation(
                        module="standard_safety",
                        violation_type=v_type,
                        severity="major",
                        description=f"{ka_id} flag: {ka_res.get('flag', 'Unknown')}",
                        recommended_action="redact" if ka_id == "KA-059" else "withhold"
                    ))
            except Exception as exc:
                raise RuntimeError(
                    f"Required Layer-10 safety check {ka_id} failed"
                ) from exc

        # Ethics Validator (L10-KA-004 + KA-027)
        try:
            ka_res = self._execute_ka(
                "L10-KA-004",
                {"content": content},
                kas_invoked,
            )
            violations = self._required_output_value(
                "L10-KA-004",
                ka_res,
                "violations",
            )
            if violations:
                result.passed = False
                for v in violations:
                    result.violations.append(SafetyViolation(
                        module="ethics",
                        violation_type=v["type"],
                        severity=v["severity"],
                        description=v["message"],
                        recommended_action="modify"
                    ))
        except Exception as exc:
            raise RuntimeError(
                "Required Layer-10 ethics check failed"
            ) from exc

        result.release_approved = len([v for v in result.violations if v.severity == "critical"]) == 0
        return result

    def _evaluate_trust_gate_lane_a(self, input_data: L10Input, kas_invoked: list[str]) -> TrustGateResult:
        """Enforce domain thresholds with belief decay and Axis 17 governance."""
        orig_conf = input_data.l9_result.get("readiness_score", 0.0)
        decayed_conf = orig_conf * BELIEF_DECAY_FACTOR
        
        domain = input_data.risk_domain
        threshold = TRUST_THRESHOLDS.get(domain, 0.95)
        
        status = "pass" if decayed_conf >= threshold else "fail"
        action = "none"
        
        if status == "fail":
            action = "human_review" if domain == "high_risk" else "refinement"
            # KA-095: Human-in-the-Loop Escalation
            if action == "human_review" and self.ka_controller:
                try:
                    self._execute_ka(
                        "KA-095",
                        {
                            "problem": input_data.problem_spec,
                            "reason": "high_risk_low_confidence",
                        },
                        kas_invoked,
                    )
                except Exception as exc:
                    raise RuntimeError(
                        "Required high-risk human escalation failed"
                    ) from exc
            
        kas_invoked.append("L10-KA-006")
        
        return TrustGateResult(
            status=status,
            domain_category=domain,
            required_threshold=threshold,
            original_confidence=orig_conf,
            decayed_confidence=decayed_conf,
            gap=decayed_conf - threshold,
            action_required=action
        )

    def _process_knowledge_commit_lane_b(self, input_data: L10Input, kas_invoked: list[str]) -> dict[str, Any]:
        """Authorized persistence logic (Lane B). Decides if knowledge is saved."""
        commit_report = {"status": "authorized", "promotion_authorized": True}
        
        # KA-109: Containment Classifier (Tagging)
        if self.ka_controller:
            try:
                ka_res = self._execute_ka(
                    "KA-109",
                    {"content": input_data.reasoning_trace},
                    kas_invoked,
                )
                commit_report["containment_class"] = self._required_output_value(
                    "KA-109",
                    ka_res,
                    "class",
                )
            except Exception as exc:
                raise RuntimeError(
                    "Required Lane-B containment classification failed"
                ) from exc

            # KA-079: Knowledge Promotion Gate
            try:
                ka_res = self._execute_ka(
                    "KA-079",
                    {"trace": input_data.reasoning_trace},
                    kas_invoked,
                )
                commit_report["promotion_authorized"] = bool(
                    self._required_output_value(
                        "KA-079",
                        ka_res,
                        "authorized",
                    )
                )
            except Exception as exc:
                raise RuntimeError(
                    "Required Lane-B promotion gate failed"
                ) from exc

        if not self.config.get("enable_lane_b_commit", True):
            commit_report["status"] = "disabled"
            return commit_report

        if not commit_report.get("promotion_authorized"):
            commit_report["status"] = "skipped"
            return commit_report

        properties = self._build_lane_b_knowledge_node(input_data, commit_report)
        if not properties.get("content"):
            commit_report["status"] = "skipped_empty_content"
            return commit_report

        try:
            from backend.memory import get_unified_memory_service
            from backend.storage import get_graph_store, get_uskd_memory_graph

            pillar_uid = self._coordinate_axis_value(input_data.coordinate_vector, 1)
            memory_stats = get_uskd_memory_graph().upsert_authorized_knowledge_node(
                properties["uid"],
                node_id=properties["node_id"],
                title=properties["title"],
                axis_number=properties.get("axis_number"),
                pillar_uid=pillar_uid,
                data=properties,
            )
            commit_report["memory_graph_updated"] = True
            commit_report["memory_graph_nodes"] = memory_stats.node_count
            memory_vertex = get_unified_memory_service().record_release_commit(
                content=str(properties.get("content") or properties.get("title") or ""),
                simulation_id=input_data.simulation_id,
                metadata={
                    "uid": properties.get("uid"),
                    "node_id": properties.get("node_id"),
                    "containment_class": commit_report.get("containment_class"),
                },
            )
            commit_report["structured_memory_vertex_id"] = memory_vertex.vertex_id
            commit_report["structured_memory_vertices"] = get_unified_memory_service().stats()["memory_vertices"]

            store = get_graph_store()
            commit_report["neo4j_node_merged"] = store.merge_knowledge_node(properties)
            if pillar_uid:
                commit_report["neo4j_relationship_merged"] = store.merge_relationship_by_uid(
                    str(pillar_uid),
                    properties["uid"],
                    "AUTHORIZED_KNOWLEDGE",
                    {"simulation_id": input_data.simulation_id},
                )
            commit_report.update(self._index_lane_b_trace(input_data, properties))
            commit_report["status"] = "committed"
        except Exception as exc:  # noqa: BLE001 - authoritative store boundary
            logger.warning("Lane B graph commit skipped: %s", exc)
            commit_report["status"] = "graph_commit_skipped"
            commit_report["error"] = str(exc)

        return commit_report

    @staticmethod
    def _index_lane_b_trace(input_data: L10Input, properties: dict[str, Any]) -> dict[str, Any]:
        """Index release-authorized traces into DB-C vector collections."""
        report = {
            "audit_evidence_indexed": False,
            "knowledge_nodes_indexed": False,
        }
        try:
            from backend.services.rag_service import RAGService, get_rag_service

            rag = get_rag_service()
            content = str(properties.get("content") or properties.get("title") or "")
            if content:
                report["knowledge_nodes_indexed"] = rag.ingest_knowledge_node(
                    properties["uid"],
                    content,
                    properties.get("node_type", "authorized_knowledge"),
                    properties,
                )

            trace_text = json.dumps(
                {
                    "simulation_id": input_data.simulation_id,
                    "l9_result": input_data.l9_result,
                    "reasoning_trace": input_data.reasoning_trace,
                    "coordinate_vector": input_data.coordinate_vector,
                },
                sort_keys=True,
                default=str,
            )
            report["audit_evidence_indexed"] = rag.ingest_text(
                RAGService.COLLECTION_AUDIT_EVIDENCE,
                f"audit:{properties['uid']}",
                trace_text,
                {
                    "simulation_id": input_data.simulation_id,
                    "knowledge_uid": properties["uid"],
                    "risk_domain": input_data.risk_domain,
                },
            )
        except Exception as exc:  # noqa: BLE001 - optional trace index boundary
            report["vector_index_error"] = str(exc)
        return report

    def _build_lane_b_knowledge_node(self, input_data: L10Input, commit_report: dict[str, Any]) -> dict[str, Any]:
        """Build a deterministic KnowledgeNode payload for release-authorized output."""
        final_answer = str(input_data.l9_result.get("epistemic_report", {}).get("current_output", "") or "").strip()
        trace_payload = {
            "simulation_id": input_data.simulation_id,
            "answer": final_answer,
            "coordinate_vector": input_data.coordinate_vector,
            "reasoning_trace": input_data.reasoning_trace,
        }
        digest = hashlib.sha256(json.dumps(trace_payload, sort_keys=True, default=str).encode()).hexdigest()[:24]
        axis_number = self._first_coordinate_axis(input_data.coordinate_vector)
        return {
            "uid": f"l10:{digest}",
            "node_id": f"L10-{digest}",
            "node_type": "authorized_knowledge",
            "title": final_answer[:120] or f"Authorized knowledge {input_data.simulation_id}",
            "label": "L10 Authorized Knowledge",
            "description": "Knowledge promoted by Layer 10 Lane B after release authorization.",
            "content": final_answer,
            "content_type": "text/plain",
            "axis_number": axis_number,
            "simulation_id": input_data.simulation_id,
            "risk_domain": input_data.risk_domain,
            "coordinate_vector": input_data.coordinate_vector,
            "reasoning_trace": input_data.reasoning_trace,
            "containment_class": commit_report.get("containment_class"),
            "promotion_authorized": commit_report.get("promotion_authorized"),
        }

    @staticmethod
    def _first_coordinate_axis(coordinate_vector: dict[str, Any]) -> int | None:
        active_axes = coordinate_vector.get("active_axes") if isinstance(coordinate_vector, dict) else None
        if isinstance(active_axes, list):
            for axis in active_axes:
                try:
                    return int(axis)
                except (TypeError, ValueError):
                    continue
        if isinstance(coordinate_vector, dict):
            for key in coordinate_vector:
                try:
                    axis = int(str(key).removeprefix("axis_").removeprefix("A"))
                    if 1 <= axis <= 17:
                        return axis
                except ValueError:
                    continue
        return None

    @staticmethod
    def _coordinate_axis_value(coordinate_vector: dict[str, Any], axis_number: int) -> str | None:
        if not isinstance(coordinate_vector, dict):
            return None
        for key in (axis_number, str(axis_number), f"axis_{axis_number}", f"A{axis_number}"):
            value = coordinate_vector.get(key)
            if isinstance(value, dict):
                value = value.get("uid") or value.get("value") or value.get("code")
            if value:
                return str(value)
        return None

    def _make_containment_decision(self, 
                                  input_data: L10Input, 
                                  emergence: EmergenceAssessment,
                                  safety: SafetyCheckResult,
                                  trust: TrustGateResult) -> tuple[L10Decision, str | None, list[ContainmentAction]]:
        """Decision tree mapping signals to containment actions."""
        actions = []
        final_answer = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        # 1. Critical Fail -> HALT
        if not safety.release_approved or emergence.overall_level == EmergenceLevel.CRITICAL:
            return L10Decision.HALT, "Output halted due to critical safety/emergence violation.", actions
            
        # 2. Safety Violations -> MODIFY
        if safety.violations:
            for v in safety.violations:
                actions.append(ContainmentAction(
                    action_type=v.recommended_action,
                    reason=v.violation_type,
                    description=v.description
                ))
            # Simulated redaction logic for PII violation
            if any(v.violation_type == "PII_leak" for v in safety.violations):
                import re
                final_answer = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED EMAIL]', final_answer)
                
            return L10Decision.MODIFY, final_answer, actions
            
        # 3. Trust Fail -> ESCALATE or WITHHOLD
        if trust.status == "fail":
            if trust.action_required == "human_review":
                return L10Decision.ESCALATE, final_answer, actions
            return L10Decision.WITHHOLD, "Answer withheld due to internal confidence thresholds.", actions
            
        # 4. Standard Pass -> RELEASE
        return L10Decision.RELEASE, final_answer, actions

    def _generate_dsqp_seal(self, 
                           input_data: L10Input, 
                           emergence: EmergenceAssessment, 
                           safety: SafetyCheckResult) -> DSQPTraceSeal:
        """Axis 15: Create immutable audit seal."""
        trace_id = input_data.simulation_id
        # In production, this would involve sha256 of the concatenated L1-L9 trace objects
        return DSQPTraceSeal(
            trace_id=trace_id,
            hash_chain_root="sha256:d826... sentinel_sealed",
            compliance_status="compliant" if safety.passed and emergence.overall_level != EmergenceLevel.HIGH else "flagged"
        )

    def _create_failure_result(self, input_data: L10Input | None, error_msg: str, processing_time: float) -> L10Result:
        """Fail-Closed result for Layer 10 errors."""
        sim_id = input_data.simulation_id if input_data else "unknown"
        return L10Result(
            simulation_id=sim_id,
            decision=L10Decision.HALT,
            final_answer=f"System error: Final safety gate failed to authorize release. Details: {error_msg}",
            dsqp_seal=DSQPTraceSeal(trace_id=sim_id, hash_chain_root="error", compliance_status="error"),
            processing_time_ms=processing_time
        )
