"""
Layer 9: MetaReasoningController

The MetaReasoningController is the recursion governor of the UKG system.
It acts as the decision point (FINALIZE vs REFINE) after Layer 8,
ensuring solutions are thoroughly self-examined before release.

Key Responsibilities:
1. Trace integrity analysis (L1-L8 systematic review)
2. Belief drift detection (query vs solution alignment)
3. Persona agreement auditing (silent dissent detection)
4. Meta-cognitive self-evaluation
5. Recursion governance (target layer routing)
6. Readiness scoring and gate decision

Required KAs (L9 Suite):
- L9-KA-001: Trace Analyzer
- L9-KA-002: Belief Drift Detector
- L9-KA-003: Persona Agreement Auditor
- L9-KA-004: Meta-Cognitive Evaluator
- L9-KA-005: Recursion Trigger
- L9-KA-006: Readiness Scorer
- L9-KA-007: Loop Controller
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple

from .l9_schemas import (
    L9Decision,
    RefinementSeverity,
    BeliefDriftReport,
    PersonaAgreementItem,
    PersonaAgreementMatrix,
    TraceIntegrityReport,
    MetaEvaluationReport,
    RefinementDirective,
    RefinementPlan,
    EpistemicReport,
    L9Input,
    L9Result
)
from .historical_embeddings import cosine_similarity, parse_embedding, text_to_embedding

logger = logging.getLogger(__name__)


# Readiness thresholds
READINESS_THRESHOLDS = {
    "standard": 0.95,
    "high_risk": 0.99
}

# Persona agreement thresholds
PERSONA_THRESHOLDS = {
    "standard": 0.95,
    "high_risk": 0.99
}

# Recursion routing table: issue_type -> target_layer
RECURSION_ROUTING = {
    "knowledge_gap": 2,
    "missing_perspective": 4,
    "persona_disagreement": 5,
    "low_quantitative_support": 6,
    "robustness_issues": 7,
    "cross_domain_contradiction": 5,
    "trust_gate_fail": 8
}

# Maximum processing time
MAX_PROCESSING_TIME_MS = 30000


class MetaReasoningController:
    """
    Layer 9: MetaReasoningController
    
    Recursion governor ensuring solutions are thoroughly self-examined
    before finalization. Makes FINALIZE or REFINE gate decisions.
    """
    
    # L9 KA Suite (Layer 9 specific)
    L9_KAS = [
        "L9-KA-001",  # Trace Analyzer
        "L9-KA-002",  # Belief Drift Detector
        "L9-KA-003",  # Persona Agreement Auditor
        "L9-KA-004",  # Meta-Cognitive Evaluator
        "L9-KA-005",  # Recursion Trigger
        "L9-KA-006",  # Readiness Scorer
        "L9-KA-007",  # Loop Controller
    ]
    
    # Canonical KAs from registry (inherited from user docs)
    CANONICAL_KAS = [
        "KA-008",  # Self-Critique & Reflection
        "KA-010",  # Bias Detection
        "KA-022",  # Memory Drift
        "KA-025",  # Self-Awareness Scoring
    ]
    
    def __init__(self, ka_controller=None, config: Optional[Dict] = None):
        """
        Initialize the MetaReasoningController.
        
        Args:
            ka_controller: KA Master Controller for algorithm execution
            config: Optional configuration overrides
        """
        self.ka_controller = ka_controller
        self.config = config or {}
        
        # Thresholds
        self.readiness_thresholds = self.config.get("readiness_thresholds", READINESS_THRESHOLDS)
        self.persona_thresholds = self.config.get("persona_thresholds", PERSONA_THRESHOLDS)
        self.max_processing_time = self.config.get("max_processing_time_ms", MAX_PROCESSING_TIME_MS)
        
        # Iteration limits
        self.max_iterations = self.config.get("max_iterations", 5)
        self.min_improvement_threshold = self.config.get("min_improvement_threshold", 0.03)
        
        # Stats
        self.total_processed = 0
        self.finalize_count = 0
        self.refine_count = 0
        
        logger.info("MetaReasoningController initialized with 7 L9 KAs + 4 canonical KAs")
    
    def evaluate(self, input_data: L9Input) -> L9Result:
        """
        Execute Layer 9 meta-reasoning evaluation.
        
        Args:
            input_data: L9Input with L8 gate result and reasoning trace
            
        Returns:
            L9Result with FINALIZE or REFINE decision
        """
        start_time = time.time()
        kas_invoked = []
        
        try:
            # Get thresholds based on risk domain
            readiness_threshold = self._get_readiness_threshold(input_data)
            persona_threshold = self._get_persona_threshold(input_data)
            
            # Check iteration limits
            iteration_check = self._check_iteration_limits(input_data)
            if iteration_check:
                return iteration_check
            
            # Phase 1: Trace Integrity Analysis
            trace_report = self._analyze_trace_integrity(input_data, kas_invoked)
            
            # Phase 2: Belief Drift Detection
            drift_report = self._detect_belief_drift(input_data, kas_invoked)
            
            # Phase 3: Persona Agreement Audit
            persona_report = self._audit_persona_agreement(input_data, persona_threshold, kas_invoked)
            
            # Phase 4: Meta-Cognitive Evaluation
            meta_report = self._run_meta_evaluation(input_data, kas_invoked)
            
            # Phase 4b: Run Canonical KA Checks (KA-008, KA-010, KA-022, KA-025)
            canonical_results = self._run_canonical_ka_checks(input_data, kas_invoked)
            
            # Integrate canonical KA results into meta report
            if canonical_results.get("bias_detected"):
                meta_report.weakness_hotspots.append({
                    "area": "bias",
                    "severity": "high",
                    "description": "KA-010 detected potential bias in reasoning"
                })
            if canonical_results.get("memory_drift_score", 0) > 0.2:
                meta_report.failure_modes.append({
                    "scenario": "memory_drift",
                    "probability": canonical_results["memory_drift_score"],
                    "impact": "medium"
                })
            
            # Phase 5: Calculate Readiness Score
            readiness_score, readiness_components = self._calculate_readiness(
                input_data, trace_report, drift_report, persona_report, meta_report, kas_invoked
            )

            
            # Phase 6: Make Gate Decision
            decision, severity, refinement_plan = self._make_decision(
                readiness_score, readiness_threshold, trace_report, drift_report, 
                persona_report, meta_report, input_data, kas_invoked
            )
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Check timeout (fail-closed → REFINE)
            if processing_time_ms > self.max_processing_time:
                logger.error(f"L9 timeout: {processing_time_ms:.0f}ms > {self.max_processing_time}ms")
                decision = L9Decision.REFINE
                severity = RefinementSeverity.MAJOR
            
            # Build epistemic report for FINALIZE path
            epistemic_report = None
            if decision == L9Decision.FINALIZE:
                epistemic_report = self._generate_epistemic_report(
                    trace_report, drift_report, persona_report
                )
            
            # Build result
            result = L9Result(
                simulation_id=input_data.simulation_id,
                decision=decision,
                severity=severity,
                readiness_score=readiness_score,
                readiness_components=readiness_components,
                trace_report=trace_report,
                drift_report=drift_report,
                persona_report=persona_report,
                meta_report=meta_report,
                refinement_plan=refinement_plan,
                epistemic_report=epistemic_report,
                requires_human_review=self._requires_human_review(input_data, decision),
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time_ms
            )
            
            # Update stats
            self._update_stats(decision)
            
            logger.info(f"L9 decision: {decision.value} (readiness={readiness_score:.3f}, threshold={readiness_threshold:.3f})")
            
            return result
            
        except Exception as e:
            # Fail-closed → REFINE on error
            logger.error(f"L9 critical error, defaulting to REFINE: {e}")
            processing_time_ms = (time.time() - start_time) * 1000
            
            return L9Result(
                simulation_id=input_data.simulation_id,
                decision=L9Decision.REFINE,
                severity=RefinementSeverity.MAJOR,
                readiness_score=0.0,
                disclosure_flags=[f"L9 error: {str(e)}"],
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time_ms
            )
    
    def _get_readiness_threshold(self, input_data: L9Input) -> float:
        """Get readiness threshold based on risk domain."""
        risk_domain = input_data.risk_domain
        if risk_domain in ["healthcare", "finance", "legal", "safety"]:
            return self.readiness_thresholds.get("high_risk", 0.99)
        return self.readiness_thresholds.get("standard", 0.95)
    
    def _get_persona_threshold(self, input_data: L9Input) -> float:
        """Get persona agreement threshold based on risk domain."""
        risk_domain = input_data.risk_domain
        if risk_domain in ["healthcare", "finance", "legal", "safety"]:
            return self.persona_thresholds.get("high_risk", 0.99)
        return self.persona_thresholds.get("standard", 0.95)
    
    def _check_iteration_limits(self, input_data: L9Input) -> Optional[L9Result]:
        """Check if we've hit iteration limits."""
        iteration_state = input_data.iteration_state
        current_iter = iteration_state.get("current_iteration", 1)
        max_iter = iteration_state.get("max_iterations", self.max_iterations)
        
        # Check max iterations
        if current_iter >= max_iter:
            logger.warning(f"L9: Max iterations ({max_iter}) reached, forcing FINALIZE")
            return L9Result(
                simulation_id=input_data.simulation_id,
                decision=L9Decision.FINALIZE,
                readiness_score=0.8,  # Suboptimal but acceptable
                disclosure_flags=["Max iterations reached - answer provided with qualification"],
                processing_time_ms=1.0
            )
        
        # Check diminishing returns
        prev_scores = iteration_state.get("previous_readiness_scores", [])
        if len(prev_scores) >= 2:
            improvement = prev_scores[-1] - prev_scores[-2]
            if improvement < self.min_improvement_threshold:
                logger.info(f"L9: Diminishing returns (improvement={improvement:.3f}), stopping")
                return L9Result(
                    simulation_id=input_data.simulation_id,
                    decision=L9Decision.FINALIZE,
                    readiness_score=prev_scores[-1],
                    disclosure_flags=["Diminishing returns - refinement stopped"],
                    processing_time_ms=1.0
                )
        
        return None
    
    def _analyze_trace_integrity(self, input_data: L9Input, kas_invoked: List[str]) -> TraceIntegrityReport:
        """Analyze reasoning trace integrity (L1-L8)."""
        trace = input_data.reasoning_trace
        issues = []
        layers_reviewed = []
        
        # Check each layer in trace
        for layer_num in range(1, 9):
            layer_key = f"layer{layer_num}"
            if layer_key in trace:
                layers_reviewed.append(layer_num)
                layer_data = trace[layer_key]
                
                # Check for missing outputs
                if not layer_data.get("output"):
                    issues.append({
                        "layer": layer_num,
                        "type": "missing_output",
                        "description": f"Layer {layer_num} has no output"
                    })
        
        # KA integration (L9-KA-001)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("L9-KA-001", {
                    "trace": trace,
                    "layers": layers_reviewed
                })
                kas_invoked.append("L9-KA-001")
                # Merge any additional issues
                issues.extend(result.get("issues", []))
            except Exception as e:
                logger.debug(f"L9-KA-001 skipped: {e}")
        
        integrity_score = 1.0 - (len(issues) * 0.1)
        integrity_score = max(0.0, min(1.0, integrity_score))
        
        return TraceIntegrityReport(
            integrity_score=integrity_score,
            layers_reviewed=layers_reviewed,
            issues_found=issues,
            orphan_claims=len([i for i in issues if i.get("type") == "orphan_claim"]),
            unresolved_branches=len([i for i in issues if i.get("type") == "unresolved_branch"])
        )
    
    def _detect_belief_drift(self, input_data: L9Input, kas_invoked: List[str]) -> BeliefDriftReport:
        """Detect belief drift between original query and final solution."""
        problem_spec = input_data.problem_spec
        l8_result = input_data.l8_gate_result
        
        original_query = problem_spec.get("original_query", "")
        # Get final solution from L8 or trace
        final_solution = l8_result.get("quantum_summary", "") or str(l8_result)
        
        drift_detected = False
        drift_score = 0.0
        drift_type = None
        details = None
        
        # Simple semantic check (would use embeddings in production)
        if original_query and final_solution:
            # Check for numerical drift
            import re
            query_numbers = re.findall(r'\d+(?:\.\d+)?%?', original_query)
            solution_numbers = re.findall(r'\d+(?:\.\d+)?%?', final_solution)
            
            if query_numbers and solution_numbers:
                # Check if numbers significantly differ
                try:
                    for qn in query_numbers:
                        qn_val = float(qn.replace('%', ''))
                        for sn in solution_numbers:
                            sn_val = float(sn.replace('%', ''))
                            if abs(qn_val - sn_val) / max(qn_val, 1) > 0.2:
                                drift_detected = True
                                drift_type = "numerical"
                                drift_score = 0.3
                                details = f"Query: {qn}, Solution: {sn}"
                                break
                except (TypeError, ValueError):
                    pass

            historical_matches = self._search_audit_evidence(original_query, final_solution)
            db_similar_sessions = self._search_db_similar_sessions(original_query)
            if historical_matches:
                details = details or f"Compared against {len(historical_matches)} similar prior sessions"
                if any(match.get("score", 0.0) < 0.65 for match in historical_matches):
                    drift_detected = True
                    drift_type = drift_type or "semantic"
                    drift_score = max(drift_score, 0.25)
            if db_similar_sessions:
                baseline = sum(item.get("confidence_score", 0.0) for item in db_similar_sessions) / len(db_similar_sessions)
                details = details or f"Compared against {len(db_similar_sessions)} DB historical sessions"
                if baseline < 0.70:
                    drift_detected = True
                    drift_type = drift_type or "historical_baseline"
                    drift_score = max(drift_score, 1.0 - baseline)
        else:
            db_similar_sessions = []
        
        # KA integration (L9-KA-002)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("L9-KA-002", {
                    "original_query": original_query,
                    "final_solution": final_solution[:500]
                })
                kas_invoked.append("L9-KA-002")
                if result.get("drift_detected"):
                    drift_detected = True
                    drift_score = max(drift_score, result.get("drift_score", 0.0))
                    drift_type = result.get("drift_type", drift_type)
            except Exception as e:
                logger.debug(f"L9-KA-002 skipped: {e}")
        
        return BeliefDriftReport(
            drift_detected=drift_detected,
            drift_score=drift_score,
            drift_type=drift_type,
            original_intent=original_query[:200] if original_query else None,
            current_output=final_solution[:200] if final_solution else None,
            details=details,
            db_similar_sessions=db_similar_sessions
        )

    @staticmethod
    def _search_audit_evidence(original_query: str, final_solution: str) -> List[Dict[str, Any]]:
        """Search semantically similar prior sessions from audit_evidence."""
        try:
            from backend.services.rag_service import RAGService, get_rag_service

            query = "\n".join(part for part in [original_query, final_solution[:500]] if part)
            if not query:
                return []
            return get_rag_service().search_collection(
                RAGService.COLLECTION_AUDIT_EVIDENCE,
                query,
                k=3,
            )
        except Exception:
            return []

    @staticmethod
    def _search_db_similar_sessions(original_query: str) -> List[Dict[str, Any]]:
        """Search TruthSession.input_embedding for local historical drift baseline."""
        if not original_query:
            return []
        try:
            from extensions import db
            from models import TruthSession

            current_embedding = text_to_embedding(original_query)
            rows = (
                db.session.query(TruthSession)
                .filter(TruthSession.input_embedding.isnot(None))
                .order_by(TruthSession.created_at.desc())
                .limit(100)
                .all()
            )
            matches = []
            for row in rows:
                stored_embedding = parse_embedding(row.input_embedding)
                similarity = cosine_similarity(current_embedding, stored_embedding)
                if similarity < 0.55:
                    continue
                matches.append({
                    "session_id": row.session_id,
                    "similarity": round(similarity, 4),
                    "confidence_score": float(row.confidence_score or 0.0),
                    "tier": row.tier,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            return sorted(matches, key=lambda item: item["similarity"], reverse=True)[:3]
        except Exception:
            return []
    
    def _audit_persona_agreement(self, input_data: L9Input, threshold: float, kas_invoked: List[str]) -> PersonaAgreementMatrix:
        """Audit persona agreement for silent dissent."""
        l8_result = input_data.l8_gate_result
        
        # Extract domain confidences from L8
        domain_confs = l8_result.get("domain_confidences", [])
        
        matrix = []
        min_score = 1.0
        flagged = []
        
        for dc in domain_confs:
            if isinstance(dc, dict):
                persona = dc.get("domain", "unknown")
                confidence = dc.get("confidence", 1.0)
                
                item = PersonaAgreementItem(
                    persona=persona,
                    component="overall",
                    score=confidence
                )
                matrix.append(item)
                
                if confidence < min_score:
                    min_score = confidence
                
                if confidence < threshold:
                    item.concern = f"Satisfaction {confidence:.1%} below threshold {threshold:.1%}"
                    flagged.append(item)
        
        # KA integration (L9-KA-003)
        if self.ka_controller:
            try:
                self.ka_controller.execute_algorithm("L9-KA-003", {
                    "domain_confidences": domain_confs
                })
                kas_invoked.append("L9-KA-003")
            except Exception as e:
                logger.debug(f"L9-KA-003 skipped: {e}")
        
        return PersonaAgreementMatrix(
            matrix=matrix,
            min_score=min_score,
            threshold_required=threshold,
            threshold_met=(min_score >= threshold),
            flagged_combinations=flagged
        )
    
    def _run_meta_evaluation(self, input_data: L9Input, kas_invoked: List[str]) -> MetaEvaluationReport:
        """Run meta-cognitive self-evaluation."""
        weakness_hotspots = []
        failure_modes = []
        alternatives = []
        
        # KA integration (L9-KA-004)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("L9-KA-004", {
                    "solution": input_data.l8_gate_result,
                    "trace": input_data.reasoning_trace
                })
                kas_invoked.append("L9-KA-004")
                weakness_hotspots = result.get("weaknesses", [])
                failure_modes = result.get("failure_modes", [])
                alternatives = result.get("alternatives", [])
            except Exception as e:
                logger.debug(f"L9-KA-004 skipped: {e}")
        
        # Calculate meta score
        num_issues = len(weakness_hotspots) + len(failure_modes)
        eval_score = max(0.5, 1.0 - (num_issues * 0.1))
        
        return MetaEvaluationReport(
            evaluation_score=eval_score,
            weakness_hotspots=weakness_hotspots,
            failure_modes=failure_modes,
            alternative_approaches=alternatives
        )
    
    def _run_canonical_ka_checks(self, input_data: L9Input, kas_invoked: List[str]) -> Dict[str, Any]:
        """
        Run canonical KAs from the registry (KA-008, KA-010, KA-022, KA-025).
        
        These are the regular KAs that the user's notes specify for Layer 9.
        """
        results = {
            "self_critique_score": 1.0,
            "bias_detected": False,
            "memory_drift_score": 0.0,
            "self_awareness_score": 1.0
        }
        
        if not self.ka_controller:
            return results
        
        # KA-008: Self-Critique & Reflection
        try:
            result = self.ka_controller.execute_algorithm("KA-008", {
                "output": str(input_data.l8_gate_result)[:1000],
                "context": input_data.problem_spec
            })
            kas_invoked.append("KA-008")
            results["self_critique_score"] = result.get("quality_score", 1.0)
        except Exception as e:
            logger.debug(f"KA-008 skipped: {e}")
        
        # KA-010: Bias Detection
        try:
            result = self.ka_controller.execute_algorithm("KA-010", {
                "content": str(input_data.l8_gate_result)[:500],
                "context": input_data.reasoning_trace
            })
            kas_invoked.append("KA-010")
            results["bias_detected"] = result.get("bias_detected", False)
        except Exception as e:
            logger.debug(f"KA-010 skipped: {e}")
        
        # KA-022: Memory Drift
        try:
            result = self.ka_controller.execute_algorithm("KA-022", {
                "original_context": input_data.problem_spec,
                "current_state": input_data.l8_gate_result
            })
            kas_invoked.append("KA-022")
            results["memory_drift_score"] = result.get("drift_score", 0.0)
        except Exception as e:
            logger.debug(f"KA-022 skipped: {e}")
        
        # KA-025: Self-Awareness Scoring
        try:
            result = self.ka_controller.execute_algorithm("KA-025", {
                "system_state": input_data.l8_gate_result,
                "trace": input_data.reasoning_trace
            })
            kas_invoked.append("KA-025")
            results["self_awareness_score"] = result.get("awareness_score", 1.0)
        except Exception as e:
            logger.debug(f"KA-025 skipped: {e}")
        
        return results

    
    def _calculate_readiness(
        self,
        input_data: L9Input,
        trace_report: TraceIntegrityReport,
        drift_report: BeliefDriftReport,
        persona_report: PersonaAgreementMatrix,
        meta_report: MetaEvaluationReport,
        kas_invoked: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate composite readiness score."""
        
        # Get L8 confidence
        l8_confidence = input_data.l8_gate_result.get("overall_confidence", 0.9)
        
        # Components with weights
        components = {
            "l8_confidence": l8_confidence,
            "trace_integrity": trace_report.integrity_score,
            "belief_alignment": 1.0 - drift_report.drift_score,
            "persona_agreement": persona_report.min_score,
            "meta_evaluation": meta_report.evaluation_score
        }
        
        # Weighted readiness calculation
        readiness = (
            0.30 * components["l8_confidence"] +
            0.15 * components["trace_integrity"] +
            0.20 * components["belief_alignment"] +
            0.25 * components["persona_agreement"] +
            0.10 * components["meta_evaluation"]
        )
        
        # KA integration (L9-KA-006)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("L9-KA-006", components)
                kas_invoked.append("L9-KA-006")
                readiness = result.get("readiness_score", readiness)
            except Exception as e:
                logger.debug(f"L9-KA-006 skipped: {e}")
        
        return readiness, components
    
    def _make_decision(
        self,
        readiness_score: float,
        threshold: float,
        trace_report: TraceIntegrityReport,
        drift_report: BeliefDriftReport,
        persona_report: PersonaAgreementMatrix,
        meta_report: MetaEvaluationReport,
        input_data: L9Input,
        kas_invoked: List[str]
    ) -> Tuple[L9Decision, Optional[RefinementSeverity], Optional[RefinementPlan]]:
        """Make FINALIZE or REFINE decision."""
        
        # Determine issues and target layer for refinement
        issues = []
        target_layer = 5  # Default
        
        # Critical failures → REFINE (MAJOR)
        if drift_report.drift_detected and drift_report.drift_score >= 0.3:
            issues.append(("belief_drift", 5, "Significant belief drift detected"))
        
        if not persona_report.threshold_met:
            for flagged in persona_report.flagged_combinations:
                issues.append(("persona_disagreement", 5, f"{flagged.persona}: {flagged.concern}"))
        
        if trace_report.integrity_score < 0.8:
            issues.append(("trace_integrity", 3, "Trace integrity issues detected"))
        
        # KA integration (L9-KA-005 + L9-KA-007)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("L9-KA-005", {
                    "readiness": readiness_score,
                    "issues": issues
                })
                kas_invoked.append("L9-KA-005")
                if result.get("trigger_refinement"):
                    issues.append(("ka_triggered", result.get("target_layer", 5), result.get("reason", "")))
            except Exception as e:
                logger.debug(f"L9-KA-005 skipped: {e}")
        
        # Decision logic
        if readiness_score >= threshold and not issues:
            return L9Decision.FINALIZE, None, None
        
        # Determine severity and target layer
        if readiness_score < threshold * 0.9 or len(issues) >= 2:
            severity = RefinementSeverity.MAJOR
        else:
            severity = RefinementSeverity.MINOR
        
        # Pick target layer from routing table
        if issues:
            issue_type = issues[0][0]
            target_layer = RECURSION_ROUTING.get(issue_type, 5)
        
        # Build refinement plan
        refinement_plan = RefinementPlan(
            target_layer=target_layer,
            preserve_layers=list(range(1, target_layer)),
            rerun_layers=list(range(target_layer, 9)),
            directives=RefinementDirective(
                focus=issues[0][2] if issues else "General refinement needed",
                required_changes=[i[2] for i in issues],
                success_criteria=f"Readiness score >= {threshold}"
            ),
            iteration_count=input_data.iteration_state.get("current_iteration", 1) + 1,
            max_iterations=self.max_iterations,
            expected_improvement=0.05
        )
        
        return L9Decision.REFINE, severity, refinement_plan
    
    def _generate_epistemic_report(
        self,
        trace_report: TraceIntegrityReport,
        drift_report: BeliefDriftReport,
        persona_report: PersonaAgreementMatrix
    ) -> EpistemicReport:
        """Generate epistemic report for finalize path."""
        return EpistemicReport(
            trace_integrity=trace_report.integrity_score,
            belief_alignment="strong" if not drift_report.drift_detected else "weak",
            persona_consensus="unanimous" if persona_report.threshold_met else "partial",
            robustness="high" if trace_report.integrity_score >= 0.95 else "medium"
        )
    
    def _requires_human_review(self, input_data: L9Input, decision: L9Decision) -> bool:
        """Determine if human review is required."""
        # High-risk domain + REFINE = human review
        if input_data.risk_domain in ["healthcare", "finance", "legal", "safety"]:
            if decision == L9Decision.REFINE:
                return True
        return False
    
    def _update_stats(self, decision: L9Decision):
        """Update internal stats."""
        self.total_processed += 1
        if decision == L9Decision.FINALIZE:
            self.finalize_count += 1
        else:
            self.refine_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics."""
        return {
            "total_processed": self.total_processed,
            "finalize_count": self.finalize_count,
            "refine_count": self.refine_count,
            "finalize_rate": self.finalize_count / max(1, self.total_processed),
            "refine_rate": self.refine_count / max(1, self.total_processed)
        }


# Factory function
def create_meta_reasoning_controller(ka_controller=None) -> MetaReasoningController:
    """Create a configured MetaReasoningController instance."""
    return MetaReasoningController(ka_controller=ka_controller)
