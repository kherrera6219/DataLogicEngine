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

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from backend.knowledge_algorithms.consumer import (
    execute_required_ka,
    require_output_field,
)

from .l8_schemas import (
    ContradictionItem,
    DomainConfidence,
    FixDirective,
    GateDecision,
    L8GateResult,
    L8Input,
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


def _jsonish(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str)


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
    
    def __init__(self, ka_controller=None, config: dict | None = None):
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

    def _execute_ka(
        self,
        ka_id: str,
        payload: dict[str, Any],
        kas_invoked: list[str],
    ):
        result = execute_required_ka(self.ka_controller, ka_id, payload)
        kas_invoked.append(result.canonical_id)
        return result
    
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
            screening_result = self._evaluate_model_screening(input_data)
            result.model_screening = screening_result
            if screening_result.get("action") == "block":
                result.status = GateDecision.FAIL
                result.warnings.append("Enhanced model screening blocked TruthGate release")
                for risk in screening_result.get("risks", []):
                    result.fix_directives.append(
                        FixDirective(
                            target_layer=8,
                            reason=f"Enhanced model screening risk: {risk}",
                            priority="critical",
                        )
                    )
                result.disclosure_required = True
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
                warnings=[f"Critical error: {e!s}"],
                fix_directives=[FixDirective(
                    target_layer=8,
                    reason=f"L8 crashed: {e!s}",
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

    def _get_historical_threshold(self, domain: str) -> float | None:
        """Calibrate thresholds from 90-day TraceRun confidence history by domain."""
        confidences = self._trace_confidences_for_domain(domain)
        if not confidences:
            return None

        static_threshold = self.risk_thresholds.get(domain, self.risk_thresholds.get("standard", 0.95))
        calibrated = mean(confidences) + 0.03
        return max(0.80, min(static_threshold, round(calibrated, 4)))

    def _trace_confidences_for_domain(self, domain: str) -> list[float]:
        session = self._get_db_session()
        if session is None:
            return []

        try:
            from models import TraceRun

            cutoff = datetime.now(UTC) - timedelta(days=90)
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
    def _domain_from_snapshot(snapshot: dict[str, Any]) -> str:
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
    
    def _run_consistency_scan(self, input_data: L8Input, kas_invoked: list[str]) -> list[ContradictionItem]:
        """Run contradiction detection on claims."""
        contradictions = []
        
        # KA-026: Contradiction Detection
        if self.ka_controller:
            try:
                findings = [
                    {
                        "id": str(index),
                        "content": claim.get("text", str(claim)),
                        "persona": claim.get("persona"),
                        "subject": claim.get("subject"),
                    }
                    for index, claim in enumerate(input_data.claims[:50])
                ]
                result = self._execute_ka(
                    "KA-026",
                    {"findings": findings},
                    kas_invoked,
                )
                
                for c in require_output_field(result, "conflicts"):
                    if "severity" not in c:
                        raise RuntimeError(
                            "KA-026 conflict is missing severity"
                        )
                    contradictions.append(ContradictionItem(
                        claim_a=str(c.get("f1_id") or ""),
                        claim_b=str(c.get("f2_id") or ""),
                        severity=c["severity"],
                    ))
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-026 contradiction scan failed"
                ) from exc
        
        # KA-030: Attempt resolution if permitted
        if contradictions and self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-030",
                    {
                        "conflicts": [c.model_dump() for c in contradictions],
                        "query": input_data.query_text,
                        "context": {"risk_domain": input_data.risk_domain},
                    },
                    kas_invoked,
                )
                resolved_findings = require_output_field(
                    result,
                    "resolved_findings",
                )
                
                for i, c in enumerate(contradictions):
                    if (
                        i < len(resolved_findings)
                        and resolved_findings[i].get("status")
                        in {"RESOLVED", "MEDIATED"}
                    ):
                        c.resolution_attempted = True
                        c.resolution_status = "resolved"
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-030 conflict resolution failed"
                ) from exc
        
        return contradictions
    
    def _run_cross_domain_validation(self, input_data: L8Input, kas_invoked: list[str]) -> list[DomainConfidence]:
        """Validate consistency across domains (Axis 6/7 crosswalks)."""
        domain_confidences = []
        
        # Base confidence from persona results
        persona_confidences = {}
        for domain in ("knowledge", "sector", "regulatory", "compliance"):
            raw_confidence = input_data.persona_results.get(domain, {}).get(
                "confidence"
            )
            persona_confidences[domain] = (
                float(raw_confidence)
                if isinstance(raw_confidence, (int, float))
                else 0.0
            )
        
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
                result = self._execute_ka(
                    "KA-016",
                    {
                        "query": input_data.query_text,
                        "frameworks": [
                            str(item)
                            for item in input_data.constraints
                            if isinstance(item, str)
                        ],
                    },
                    kas_invoked,
                )
                
                reg_conf = 1.0 - float(
                    require_output_field(result, "highest_risk")
                )
                domain_confidences.append(DomainConfidence(
                    domain="regulatory_mapping",
                    axis_id=6,
                    confidence=reg_conf,
                    threshold=threshold,
                    passes=reg_conf >= threshold
                ))
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-016 regulatory mapping failed"
                ) from exc
        
        # KA-025: Dependency Mapping (Axis 7)
        if self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-025",
                    {
                        "nodes": [
                            {
                                "id": str(
                                    claim.get("id")
                                    or claim.get("claim_id")
                                    or index
                                ),
                                "deps": claim.get("dependencies", []),
                            }
                            for index, claim in enumerate(
                                input_data.claims[:20]
                            )
                        ]
                    },
                    kas_invoked,
                )
                
                dependency_meta = require_output_field(result, "meta")
                if "is_dag" not in dependency_meta:
                    raise RuntimeError(
                        "KA-025 output is missing meta.is_dag"
                    )
                dep_conf = 1.0 if dependency_meta["is_dag"] else 0.0
                domain_confidences.append(DomainConfidence(
                    domain="dependency_crosswalk",
                    axis_id=7,
                    confidence=dep_conf,
                    threshold=threshold,
                    passes=dep_conf >= threshold
                ))
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-025 dependency mapping failed"
                ) from exc
        
        return domain_confidences
    
    def _compute_trust_score(self, input_data: L8Input, domain_confidences: list[DomainConfidence], kas_invoked: list[str]) -> float:
        """Compute calibrated trust score."""
        # Start with average of domain confidences
        if domain_confidences:
            base_confidence = sum(d.confidence for d in domain_confidences) / len(domain_confidences)
        else:
            base_confidence = 0.0

        citation_hits = self._search_citation_cache(input_data)
        if citation_hits:
            kas_invoked.append("RAG-CITATION-CACHE")
            base_confidence = min(1.0, base_confidence + min(0.05, len(citation_hits) * 0.01))
        
        # KA-014: Confidence Scoring
        if self.ka_controller:
            try:
                domain_scores = {
                    item.domain: item.confidence
                    for item in domain_confidences
                }
                persona_scores = [
                    item.confidence
                    for item in domain_confidences
                    if item.domain
                    in {"knowledge", "sector", "regulatory", "compliance"}
                ]
                result = self._execute_ka(
                    "KA-014",
                    {
                        "evidence_score": min(
                            1.0,
                            len(input_data.evidence) / max(
                                len(input_data.claims),
                                1,
                            ),
                        ),
                        "persona_consensus_score": (
                            sum(persona_scores) / len(persona_scores)
                            if persona_scores
                            else 0.0
                        ),
                        "truth_score": base_confidence,
                        "relevance_score": base_confidence,
                        "has_contradictions": False,
                        "domain_scores": domain_scores,
                        "risk_domain": input_data.risk_domain,
                    },
                    kas_invoked,
                )
                base_confidence = float(
                    require_output_field(result, "calibrated_confidence")
                )
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-014 confidence calibration failed"
                ) from exc
        
        # KA-023: Belief Decay (overconfidence protection)
        if self.ka_controller:
            try:
                reference_time = datetime.now(UTC)
                # Format evidence as bounded belief observations.
                knowledge_items = [
                    {
                        "knowledge_id": str(i),
                        "current_confidence": base_confidence,
                        "observed_at": reference_time.isoformat(),
                        "category": "evidence",
                    }
                    for i, _ in enumerate(input_data.evidence[:10])
                ]
                result = self._execute_ka(
                    "KA-023",
                    {
                        "knowledge_items": knowledge_items,
                        "reference_time": reference_time.isoformat(),
                    },
                    kas_invoked,
                )
                # Calculate decay from processed items
                proposals = require_output_field(result, "proposals")
                if proposals:
                    if any("proposed_confidence" not in item for item in proposals):
                        raise RuntimeError(
                            "KA-023 proposal is missing proposed confidence"
                        )
                    avg_conf = sum(
                        float(item["proposed_confidence"])
                        for item in proposals
                    ) / len(proposals)
                    base_confidence = avg_conf
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-023 belief-decay calculation failed"
                ) from exc
        
        # KA-022: Risk Assessment
        if self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-022",
                    {
                        "recommendation": (
                            _jsonish(input_data.l5_synthesis)
                            or input_data.query_text
                        ),
                        "impact_scores": {},
                    },
                    kas_invoked,
                )
                overall_risk = float(
                    require_output_field(result, "overall_risk_score")
                )
                risk_factor = max(0.0, 1.0 - overall_risk)
                base_confidence *= risk_factor
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-022 risk assessment failed"
                ) from exc
        
        # KA-024: Trust Gate (final policy enforcement)
        if self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-024",
                    {
                        "confidence": base_confidence,
                        "risk_score": 1.0 - base_confidence,
                    },
                    kas_invoked,
                )
                # If not approved, reduce confidence significantly
                if not require_output_field(result, "is_approved"):
                    base_confidence *= 0.7
                    logger.info(
                        "KA-024 vetoed: %s",
                        require_output_field(result, "blocking_reasons"),
                    )
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-024 trust gate failed"
                ) from exc
        
        return min(max(base_confidence, 0.0), 1.0)

    @staticmethod
    def _search_citation_cache(input_data: L8Input) -> list[dict[str, Any]]:
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
    
    def _run_self_critique(self, input_data: L8Input, kas_invoked: list[str]) -> list[str]:
        """Attack the solution for flaws."""
        warnings = []
        
        # KA-008: Self-Critique & Reflection
        if self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-008",
                    {
                        "output_content": _jsonish(
                            input_data.l7_agi_plan
                            or input_data.l5_synthesis
                        )
                        or input_data.query_text
                        or "No candidate content supplied.",
                        "query": input_data.query_text,
                        "required_points": [
                            str(claim.get("text") or claim)
                            for claim in input_data.claims[:20]
                        ],
                    },
                    kas_invoked,
                )
                warnings.extend(
                    str(item)
                    for item in require_output_field(
                        result,
                        "suggestions",
                    )
                )
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-008 self-critique failed"
                ) from exc
        
        # KA-034: Adversarial Reasoning
        if self.ka_controller:
            try:
                assumptions = [
                    claim.get("text", str(claim))
                    for claim in input_data.claims[:10]
                ]
                result = self._execute_ka(
                    "KA-034",
                    {
                        "scenario": input_data.query_text,
                        "assumptions": assumptions,
                        "evidence": input_data.evidence[:20],
                    },
                    kas_invoked,
                )
                attacks = require_output_field(
                    result,
                    "attacks_simulated",
                )
                warnings.extend(
                    str(item.get("mitigation"))
                    for item in attacks
                    if item.get("vulnerability_found")
                    and item.get("mitigation")
                )
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-034 adversarial reasoning failed"
                ) from exc
        
        # KA-003: Gap Analysis
        if self.ka_controller:
            try:
                result = self._execute_ka(
                    "KA-003",
                    {
                        "current_state": {
                            "evidence_count": len(input_data.evidence),
                            "claim_count": len(input_data.claims),
                        },
                        "desired_state": {
                            "evidence_count": len(input_data.claims),
                            "claim_count": len(input_data.claims),
                        },
                    },
                    kas_invoked,
                )
                gaps = require_output_field(result, "gaps")
                if gaps:
                    warnings.append(
                        f"Evidence gaps detected: {len(gaps)} items"
                    )
            except Exception as exc:
                raise RuntimeError(
                    "Required KA-003 gap analysis failed"
                ) from exc
        
        return warnings
    
    def _make_gate_decision(
        self,
        confidence: float,
        threshold: float,
        contradictions: list[ContradictionItem],
        warnings: list[str]
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
    def _evaluate_opa_policy(input_data: L8Input, result: L8GateResult) -> dict[str, Any]:
        try:
            from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator

            return OPAPolicyEvaluator().evaluate(
                {
                    "simulation_id": input_data.simulation_id,
                    "risk_domain": input_data.risk_domain,
                    "overall_confidence": result.overall_confidence,
                    "minimum_confidence": result.target_threshold,
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

    @staticmethod
    def _evaluate_model_screening(input_data: L8Input) -> dict[str, Any]:
        try:
            from backend.truth_engine.truth_gate.model_screening import (
                TruthGateModelScreening,
            )

            claim_text = "\n".join(str(claim.get("text", claim)) for claim in input_data.claims[:20])
            synthesis_text = _jsonish(input_data.l5_synthesis)
            plan_text = _jsonish(input_data.l7_agi_plan)
            text = "\n".join(
                part
                for part in [input_data.query_text, claim_text, synthesis_text, plan_text]
                if part
            )
            return TruthGateModelScreening().screen(
                text,
                metadata={
                    "simulation_id": input_data.simulation_id,
                    "risk_domain": input_data.risk_domain,
                },
            )
        except Exception as exc:
            return {
                "enabled": False,
                "allowed": False,
                "risks": ["model_screening_error"],
                "action": "block",
                "backend": "error",
                "error": str(exc),
            }
    
    def _get_escalation_target(self, fix_directives: list[FixDirective]) -> int | None:
        """Determine which layer to escalate to."""
        if not fix_directives:
            return None
        
        # Return highest priority directive's target
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_directives = sorted(fix_directives, key=lambda d: priority_order.get(d.priority, 99))
        return sorted_directives[0].target_layer if sorted_directives else None
    
    def _get_axes_evaluated(self, input_data: L8Input) -> list[int]:
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
    
    def get_stats(self) -> dict[str, Any]:
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
