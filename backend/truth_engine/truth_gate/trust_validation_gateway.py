"""
Layer 8: Trust Validation Gateway

The TrustValidationGateway is the global trust gate of the UKG system.
It acts as a hard gate (PASS/WARN/FAIL) between Layer 7 and Layer 9,
ensuring cross-domain consistency, calibrated confidence, and enterprise trust.

Key Responsibilities:
1. Cross-domain consistency validation (Axes 6, 7)
2. Contradiction detection and conflict reporting
3. Trust calibration and threshold enforcement
4. Structured gate decisions with fix directives
5. 17-axis governance support

Required KAs:
- KA-003: Gap Analysis
- KA-008: Self-Critique & Reflection
- KA-014: Confidence Scoring
- KA-016: Regulatory Mapping
- KA-017: Spatial Jurisdiction Mapping
- KA-022: Risk Assessment
- KA-023: Belief Decay
- KA-024: Trust Gate
- KA-025: Dependency Mapping
- KA-026: Contradiction Detection
- KA-030: Conflict Resolution
- KA-034: Adversarial Reasoning
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, List, Any, Optional

from .l8_schemas import (
    GateDecision,
    ContradictionItem,
    FixDirective,
    DomainConfidence,
    L8Input,
    L8GateResult
)

logger = logging.getLogger(__name__)


# Risk-domain confidence thresholds
RISK_THRESHOLDS = {
    "standard": 0.95,
    "healthcare": 0.995,
    "finance": 0.995,
    "legal": 0.995,
    "safety": 0.995
}

# Maximum processing time (fail-closed on timeout)
MAX_PROCESSING_TIME_MS = 30000


def _elapsed_ms(start_time: float) -> float:
    """Return a positive monotonic elapsed duration for audit results."""
    return max((time.perf_counter() - start_time) * 1000, 0.001)


class TrustValidationGateway:
    """
    Layer 8: Trust Validation Gateway
    
    Global trust gate ensuring cross-domain consistency and calibrated confidence
    before forwarding to Layer 9 governance.
    
    Gate Decisions:
    - PASS: Confidence ≥ threshold, no contradictions
    - WARN: Acceptable but flagged (disclosures required)
    - FAIL: Halt finalization, emit fix directives
    """
    
    # KAs used by Layer 8
    REQUIRED_KAS = [
        "KA-003",  # Gap Analysis
        "KA-008",  # Self-Critique & Reflection
        "KA-014",  # Confidence Scoring
        "KA-016",  # Regulatory Mapping
        "KA-017",  # Spatial Jurisdiction Mapping
        "KA-022",  # Risk Assessment
        "KA-023",  # Belief Decay
        "KA-024",  # Trust Gate
        "KA-025",  # Dependency Mapping
        "KA-026",  # Contradiction Detection
        "KA-030",  # Conflict Resolution
        "KA-034",  # Adversarial Reasoning
    ]
    
    def __init__(self, ka_controller=None, config: Optional[Dict] = None):
        """
        Initialize the Trust Validation Gateway.
        
        Args:
            ka_controller: KA Master Controller for algorithm execution
            config: Optional configuration overrides
        """
        self.ka_controller = ka_controller
        self.config = config or {}
        
        # Thresholds
        self.risk_thresholds = self.config.get("risk_thresholds", RISK_THRESHOLDS)
        self.db_session = self.config.get("db_session")
        self.max_processing_time = self.config.get("max_processing_time_ms", MAX_PROCESSING_TIME_MS)
        
        # 17-axis mode
        self.enable_17_axis = self.config.get("enable_17_axis", True)
        
        # Stats
        self.total_processed = 0
        self.pass_count = 0
        self.warn_count = 0
        self.fail_count = 0
        
        logger.info("TrustValidationGateway initialized with 12 KAs")
    
    def validate(self, input_data: L8Input) -> L8GateResult:
        """
        Execute Layer 8 trust validation.
        
        Args:
            input_data: L8Input with claims, evidence, and layer artifacts
            
        Returns:
            L8GateResult with gate decision and audit artifacts
        """
        start_time = time.perf_counter()
        kas_invoked = []
        
        try:
            # Determine threshold based on risk domain
            threshold = self._get_threshold(input_data)
            
            # Phase 1: Consistency Scan (Contradictions)
            contradictions = self._run_consistency_scan(input_data, kas_invoked)
            
            # Phase 2: Cross-Domain Validation (Axes 6, 7)
            domain_confidences = self._run_cross_domain_validation(input_data, kas_invoked)
            
            # Phase 3: Trust Computation
            overall_confidence = self._compute_trust_score(input_data, domain_confidences, kas_invoked)
            
            # Phase 4: Self-Critique (Attack the solution)
            warnings = self._run_self_critique(input_data, kas_invoked)
            
            # Phase 5: Gate Decision
            status, fix_directives = self._make_gate_decision(
                overall_confidence, threshold, contradictions, warnings
            )
            
            # Calculate processing time
            processing_time_ms = _elapsed_ms(start_time)
            
            # Check timeout (fail-closed)
            if processing_time_ms > self.max_processing_time:
                logger.error(f"L8 timeout: {processing_time_ms:.0f}ms > {self.max_processing_time}ms")
                status = GateDecision.FAIL
                fix_directives.append(FixDirective(
                    target_layer=8,
                    reason="Processing timeout - fail-closed",
                    priority="critical"
                ))
            
            # Build result
            result = L8GateResult(
                simulation_id=input_data.simulation_id,
                status=status,
                overall_confidence=overall_confidence,
                target_threshold=threshold,
                domain_confidences=domain_confidences,
                quantum_trust_fidelity=overall_confidence,  # Legacy compatibility
                contradictions=contradictions,
                warnings=warnings,
                fix_directives=fix_directives,
                escalation_target=self._get_escalation_target(fix_directives),
                axes_evaluated=self._get_axes_evaluated(input_data),
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time_ms,
                requires_human_review=input_data.axis_17_requires_human,
                disclosure_required=(status == GateDecision.WARN)
            )
            opa_result = self._evaluate_opa_policy(input_data, result)
            result.opa_policy = opa_result
            if not opa_result.get("allow", True):
                result.status = GateDecision.FAIL
                result.warnings.append("OPA policy denied TruthGate release")
                for violation in opa_result.get("violations", []):
                    result.fix_directives.append(
                        FixDirective(
                            target_layer=8,
                            reason=f"OPA policy violation: {violation}",
                            priority="critical",
                        )
                    )
                result.disclosure_required = True
            
            # Update stats
            self._update_stats(status)
            
            logger.info(f"L8 gate decision: {status.value} (confidence={overall_confidence:.3f}, threshold={threshold:.3f})")
            
            return result
            
        except Exception as e:
            # Fail-closed on any error
            logger.error(f"L8 critical error, fail-closed: {e}")
            processing_time_ms = _elapsed_ms(start_time)
            
            return L8GateResult(
                simulation_id=input_data.simulation_id,
                status=GateDecision.FAIL,
                overall_confidence=0.0,
                target_threshold=threshold if 'threshold' in dir() else 0.95,
                warnings=[f"Critical error: {str(e)}"],
                fix_directives=[FixDirective(
                    target_layer=8,
                    reason=f"L8 crashed: {str(e)}",
                    priority="critical"
                )],
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time_ms
            )
    
    def _get_threshold(self, input_data: L8Input) -> float:
        """Get confidence threshold based on risk domain."""
        # Axis 14 override takes precedence
        if input_data.axis_14_threshold is not None:
            return input_data.axis_14_threshold

        domain = input_data.risk_domain or "standard"
        calibrated = self._get_historical_threshold(domain)
        if calibrated is not None:
            return calibrated

        return self.risk_thresholds.get(domain, 0.95)

    def _get_historical_threshold(self, domain: str) -> Optional[float]:
        """Calibrate thresholds from 90-day TraceRun confidence history by domain."""
        confidences = self._trace_confidences_for_domain(domain)
        if not confidences:
            return None

        static_threshold = self.risk_thresholds.get(domain, self.risk_thresholds.get("standard", 0.95))
        calibrated = mean(confidences) + 0.03
        return max(0.80, min(static_threshold, round(calibrated, 4)))

    def _trace_confidences_for_domain(self, domain: str) -> List[float]:
        session = self._get_db_session()
        if session is None:
            return []

        try:
            from models import TraceRun

            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            rows = (
                session.query(TraceRun)
                .filter(TraceRun.created_at >= cutoff)
                .filter(TraceRun.confidence.isnot(None))
                .order_by(TraceRun.created_at.desc())
                .limit(500)
                .all()
            )
        except Exception as exc:
            logger.debug(f"L8 historical calibration skipped: {exc}")
            return []

        requested = (domain or "standard").lower()
        confidences = []
        for row in rows:
            snapshot = row.data_snapshot or {}
            row_domain = self._domain_from_snapshot(snapshot)
            if row_domain == requested:
                try:
                    confidences.append(float(row.confidence))
                except (TypeError, ValueError):
                    continue
        return confidences

    @staticmethod
    def _domain_from_snapshot(snapshot: Dict[str, Any]) -> str:
        if not isinstance(snapshot, dict):
            return "standard"
        risk = snapshot.get("risk") if isinstance(snapshot.get("risk"), dict) else {}
        value = (
            snapshot.get("risk_domain")
            or snapshot.get("domain")
            or snapshot.get("truth_domain")
            or risk.get("domain")
            or "standard"
        )
        return str(value).lower()

    def _get_db_session(self):
        if self.db_session is not None:
            return self.db_session
        try:
            from extensions import db

            return db.session
        except Exception:
            return None
    
    def _run_consistency_scan(self, input_data: L8Input, kas_invoked: List[str]) -> List[ContradictionItem]:
        """Run contradiction detection on claims."""
        contradictions = []
        
        # KA-026: Contradiction Detection
        if self.ka_controller:
            try:
                claims = [c.get("text", str(c)) for c in input_data.claims[:50]]
                result = self.ka_controller.execute_algorithm("KA-026", {"claims": claims})
                kas_invoked.append("KA-026")
                
                for c in result.get("contradictions", []):
                    contradictions.append(ContradictionItem(
                        claim_a=c.get("claim_a", ""),
                        claim_b=c.get("claim_b", ""),
                        severity=c.get("severity", 0.5)
                    ))
            except Exception as e:
                logger.debug(f"KA-026 skipped: {e}")
        
        # KA-030: Attempt resolution if permitted
        if contradictions and self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-030", {
                    "conflicts": [c.dict() for c in contradictions]
                })
                kas_invoked.append("KA-030")
                
                for i, c in enumerate(contradictions):
                    if result.get("resolved", {}).get(str(i)):
                        c.resolution_attempted = True
                        c.resolution_status = "resolved"
            except Exception as e:
                logger.debug(f"KA-030 skipped: {e}")
        
        return contradictions
    
    def _run_cross_domain_validation(self, input_data: L8Input, kas_invoked: List[str]) -> List[DomainConfidence]:
        """Validate consistency across domains (Axis 6/7 crosswalks)."""
        domain_confidences = []
        
        # Base confidence from persona results
        persona_confidences = {
            "knowledge": input_data.persona_results.get("knowledge", {}).get("confidence", 0.9),
            "sector": input_data.persona_results.get("sector", {}).get("confidence", 0.9),
            "regulatory": input_data.persona_results.get("regulatory", {}).get("confidence", 0.9),
            "compliance": input_data.persona_results.get("compliance", {}).get("confidence", 0.9),
        }
        
        threshold = self._get_threshold(input_data)
        
        for domain, conf in persona_confidences.items():
            axis_id = {"knowledge": 8, "sector": 9, "regulatory": 10, "compliance": 11}.get(domain, 8)
            domain_confidences.append(DomainConfidence(
                domain=domain,
                axis_id=axis_id,
                confidence=conf,
                threshold=threshold,
                passes=conf >= threshold
            ))
        
        # KA-016: Regulatory Mapping (Axis 6)
        if self.ka_controller and input_data.constraints:
            try:
                result = self.ka_controller.execute_algorithm("KA-016", {
                    "constraints": input_data.constraints
                })
                kas_invoked.append("KA-016")
                
                reg_conf = result.get("regulatory_confidence", 0.9)
                domain_confidences.append(DomainConfidence(
                    domain="regulatory_mapping",
                    axis_id=6,
                    confidence=reg_conf,
                    threshold=threshold,
                    passes=reg_conf >= threshold
                ))
            except Exception as e:
                logger.debug(f"KA-016 skipped: {e}")
        
        # KA-025: Dependency Mapping (Axis 7)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-025", {
                    "claims": input_data.claims[:20]
                })
                kas_invoked.append("KA-025")
                
                dep_conf = result.get("dependency_confidence", 0.9)
                domain_confidences.append(DomainConfidence(
                    domain="dependency_crosswalk",
                    axis_id=7,
                    confidence=dep_conf,
                    threshold=threshold,
                    passes=dep_conf >= threshold
                ))
            except Exception as e:
                logger.debug(f"KA-025 skipped: {e}")
        
        return domain_confidences
    
    def _compute_trust_score(self, input_data: L8Input, domain_confidences: List[DomainConfidence], kas_invoked: List[str]) -> float:
        """Compute calibrated trust score."""
        # Start with average of domain confidences
        if domain_confidences:
            base_confidence = sum(d.confidence for d in domain_confidences) / len(domain_confidences)
        else:
            base_confidence = 0.9

        citation_hits = self._search_citation_cache(input_data)
        if citation_hits:
            kas_invoked.append("RAG-CITATION-CACHE")
            base_confidence = min(1.0, base_confidence + min(0.05, len(citation_hits) * 0.01))
        
        # KA-014: Confidence Scoring
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-014", {
                    "domain_scores": [d.model_dump() for d in domain_confidences],
                    "evidence_count": len(input_data.evidence)
                })
                kas_invoked.append("KA-014")
                base_confidence = result.get("calibrated_confidence", base_confidence)
            except Exception as e:
                logger.debug(f"KA-014 skipped: {e}")
        
        # KA-023: Belief Decay (overconfidence protection)
        if self.ka_controller:
            try:
                # Format evidence as knowledge_items with timestamps
                knowledge_items = [
                    {
                        "id": str(i),
                        "confidence": base_confidence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "category": "evidence"
                    }
                    for i, _ in enumerate(input_data.evidence[:10])
                ]
                result = self.ka_controller.execute_algorithm("KA-023", {
                    "knowledge_items": knowledge_items,
                    "reference_time": datetime.now(timezone.utc).isoformat()
                })
                kas_invoked.append("KA-023")
                # Calculate decay from processed items
                processed = result.get("processed_items", [])
                if processed:
                    avg_conf = sum(p.get("confidence", base_confidence) for p in processed) / len(processed)
                    base_confidence = avg_conf
            except Exception as e:
                logger.debug(f"KA-023 skipped: {e}")
        
        # KA-022: Risk Assessment
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-022", {
                    "risk_domain": input_data.risk_domain,
                    "claims": input_data.claims[:10]
                })
                kas_invoked.append("KA-022")
                risk_factor = result.get("risk_adjustment", 1.0)
                base_confidence *= risk_factor
            except Exception as e:
                logger.debug(f"KA-022 skipped: {e}")
        
        # KA-024: Trust Gate (final policy enforcement)
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-024", {
                    "confidence": base_confidence,
                    "risk_score": 1.0 - base_confidence  # Inverse of confidence
                })
                kas_invoked.append("KA-024")
                # If not approved, reduce confidence significantly
                if not result.get("is_approved", True):
                    base_confidence *= 0.7
                    logger.info(f"KA-024 vetoed: {result.get('blocking_reasons', [])}")
            except Exception as e:
                logger.debug(f"KA-024 skipped: {e}")
        
        return min(max(base_confidence, 0.0), 1.0)

    @staticmethod
    def _search_citation_cache(input_data: L8Input) -> List[Dict[str, Any]]:
        """Search prior citation evidence for similar claims or query text."""
        try:
            from backend.services.rag_service import RAGService, get_rag_service

            query_parts = [input_data.query_text]
            query_parts.extend(str(claim.get("text", claim)) for claim in input_data.claims[:3])
            query = "\n".join(part for part in query_parts if part)
            if not query:
                return []
            return get_rag_service().search_collection(
                RAGService.COLLECTION_CITATION_CACHE,
                query,
                k=3,
            )
        except Exception:
            return []
    
    def _run_self_critique(self, input_data: L8Input, kas_invoked: List[str]) -> List[str]:
        """Attack the solution for flaws."""
        warnings = []
        
        # KA-008: Self-Critique & Reflection
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-008", {
                    "solution": input_data.l7_agi_plan or input_data.l5_synthesis,
                    "claims": input_data.claims[:20]
                })
                kas_invoked.append("KA-008")
                warnings.extend(result.get("critiques", []))
            except Exception as e:
                logger.debug(f"KA-008 skipped: {e}")
        
        # KA-034: Adversarial Reasoning
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-034", {
                    "statements": [c.get("text", str(c)) for c in input_data.claims[:10]]
                })
                kas_invoked.append("KA-034")
                if result.get("vulnerabilities"):
                    warnings.extend(result.get("vulnerabilities", []))
            except Exception as e:
                logger.debug(f"KA-034 skipped: {e}")
        
        # KA-003: Gap Analysis
        if self.ka_controller:
            try:
                result = self.ka_controller.execute_algorithm("KA-003", {
                    "evidence": input_data.evidence[:20],
                    "claims": input_data.claims[:20]
                })
                kas_invoked.append("KA-003")
                if result.get("gaps"):
                    warnings.append(f"Evidence gaps detected: {len(result.get('gaps', []))} items")
            except Exception as e:
                logger.debug(f"KA-003 skipped: {e}")
        
        return warnings
    
    def _make_gate_decision(
        self,
        confidence: float,
        threshold: float,
        contradictions: List[ContradictionItem],
        warnings: List[str]
    ) -> tuple:
        """Make PASS/WARN/FAIL decision."""
        fix_directives = []
        
        # Check for critical contradictions
        critical_contradictions = [c for c in contradictions if c.severity >= 0.8 and not c.resolution_attempted]
        
        # FAIL conditions
        if critical_contradictions:
            for c in critical_contradictions:
                fix_directives.append(FixDirective(
                    target_layer=5,
                    reason=f"Critical contradiction: {c.claim_a[:50]}... vs {c.claim_b[:50]}...",
                    priority="critical",
                    suggested_action="Re-run persona debate with forced reconciliation"
                ))
            return GateDecision.FAIL, fix_directives
        
        if confidence < threshold * 0.9:  # Significantly below threshold
            fix_directives.append(FixDirective(
                target_layer=6,
                reason=f"Confidence {confidence:.3f} significantly below threshold {threshold:.3f}",
                priority="high",
                suggested_action="Re-run quant validation with expanded evidence"
            ))
            return GateDecision.FAIL, fix_directives
        
        # WARN conditions
        if confidence < threshold:
            fix_directives.append(FixDirective(
                target_layer=6,
                reason=f"Confidence {confidence:.3f} below threshold {threshold:.3f}",
                priority="medium"
            ))
            return GateDecision.WARN, fix_directives
        
        if contradictions:  # Non-critical contradictions
            return GateDecision.WARN, fix_directives
        
        if len(warnings) > 3:  # Many warnings
            return GateDecision.WARN, fix_directives
        
        # PASS
        return GateDecision.PASS, fix_directives

    @staticmethod
    def _evaluate_opa_policy(input_data: L8Input, result: L8GateResult) -> Dict[str, Any]:
        try:
            from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator

            return OPAPolicyEvaluator().evaluate(
                {
                    "simulation_id": input_data.simulation_id,
                    "risk_domain": input_data.risk_domain,
                    "overall_confidence": result.overall_confidence,
                    "status": result.status.value,
                    "axis_17_requires_human": input_data.axis_17_requires_human,
                    "human_reviewed": False,
                }
            )
        except Exception as exc:
            return {
                "available": False,
                "backend": "error",
                "allow": False,
                "violations": ["opa_evaluation_error"],
                "error": str(exc),
            }
    
    def _get_escalation_target(self, fix_directives: List[FixDirective]) -> Optional[int]:
        """Determine which layer to escalate to."""
        if not fix_directives:
            return None
        
        # Return highest priority directive's target
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_directives = sorted(fix_directives, key=lambda d: priority_order.get(d.priority, 99))
        return sorted_directives[0].target_layer if sorted_directives else None
    
    def _get_axes_evaluated(self, input_data: L8Input) -> List[int]:
        """Return list of axes evaluated."""
        axes = [6, 7, 8, 9, 10, 11, 14]  # Core axes
        if self.enable_17_axis:
            axes.extend([15, 16, 17])
        return axes
    
    def _update_stats(self, status: GateDecision):
        """Update internal stats."""
        self.total_processed += 1
        if status == GateDecision.PASS:
            self.pass_count += 1
        elif status == GateDecision.WARN:
            self.warn_count += 1
        else:
            self.fail_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "total_processed": self.total_processed,
            "pass_count": self.pass_count,
            "warn_count": self.warn_count,
            "fail_count": self.fail_count,
            "pass_rate": self.pass_count / max(1, self.total_processed),
            "fail_rate": self.fail_count / max(1, self.total_processed)
        }


# Factory function for backward compatibility
def create_trust_gateway(ka_controller=None) -> TrustValidationGateway:
    """Create a configured TrustValidationGateway instance."""
    return TrustValidationGateway(ka_controller=ka_controller)
