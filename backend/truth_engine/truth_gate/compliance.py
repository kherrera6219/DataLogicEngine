"""TruthGate technical-control evidence mapped to regulatory frameworks."""

import logging
import re
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ComplianceEnforcer:
    """
    Produce application self-check evidence for mapped technical controls.

    These checks are not a legal conclusion, independent assessment, audit,
    attestation, or certification.
    """
    
    COMPLIANCE_STANDARDS = {
        'eu_ai_act': {
            'name': 'EU AI Act',
            'articles': ['Article 53', 'Article 13'],
            'requirements': [
                'decision_logging',
                'user_explainability',
                'audit_trail',
                'pii_protection'
            ]
        },
        'gdpr': {
            'name': 'GDPR',
            'requirements': [
                'pii_redaction',
                'data_minimization',
                'right_to_explanation'
            ]
        },
        'nis2': {
            'name': 'NIS2',
            'requirements': [
                'incident_reporting',
                'risk_assessment'
            ]
        }
    }
    
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    }

    def __init__(self, db_session=None, retention_years: int = 7):
        """Initialize compliance enforcer."""
        self.db_session = db_session
        self.retention_years = retention_years
        logger.info("Control-map evidence enforcer initialized")

    def enforce(self, request: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Evaluate local technical controls without claiming legal compliance.
        """
        result = {
            'schema_version': 'dle.truth-control-evidence.v1',
            'report_classification': 'self_assessment_evidence',
            'framework_map': ['EU_AI_ACT', 'GDPR', 'NIS2'],
            'framework_map_is_certification': False,
            'session_id': session_id,
            'timestamp': datetime.now(UTC).isoformat(),
            'actions_taken': [],
        }
        
        article_53 = self._enforce_article_53(request, session_id)
        result['article_53'] = article_53
        
        article_13 = self._enforce_article_13(request, session_id)
        result['article_13'] = article_13
        
        pii_result = self._check_pii(request)
        result['pii_check'] = pii_result
        if pii_result['pii_found']:
            result['actions_taken'].append('pii_flagged')
        control_results = {
            article_53['result'],
            article_13['result'],
            pii_result['result'],
        }
        result['overall_check_result'] = (
            'checks_failed'
            if 'failed' in control_results
            else 'not_measured'
            if 'not_measured' in control_results
            else 'checks_passed'
        )
        result['certification_claim'] = False
        
        return result

    def _enforce_article_53(self, request: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Enforce Article 53: Decision logging.
        
        Log all decisions with full reasoning trace.
        """
        logged = False
        check_result = 'not_measured'
        evidence_ref = 'not_available'
        error_code = None
        
        decision_record = {
            'session_id': session_id,
            'timestamp': datetime.now(UTC).isoformat(),
            'query_hash': self._hash_query(request.get('query', '')),
            'tier': request.get('tier', 'unknown'),
            'decision_rationale': request.get('rationale', ''),
            'personas_used': request.get('personas_used', []),
            'axis_context': request.get('axis_context', {}),
            'confidence': request.get('confidence', 0),
            'retention_until': (datetime.now(UTC) + timedelta(days=365 * self.retention_years)).isoformat()
        }
        
        if self.db_session and session_id:
            try:
                from models import TruthAuditEvent
                import uuid
                import hashlib
                
                previous_event = self.db_session.query(TruthAuditEvent).filter_by(
                    session_id=session_id
                ).order_by(TruthAuditEvent.id.desc()).first()
                
                previous_hash = previous_event.hash_chain if previous_event else '0' * 64
                
                event_data = str(decision_record).encode()
                current_hash = hashlib.sha256(
                    (previous_hash + event_data.hex()).encode()
                ).hexdigest()
                
                audit_event = TruthAuditEvent(
                    event_id=str(uuid.uuid4()),
                    session_id=session_id,
                    event_type='decision_log',
                    event_category='article_53',
                    event_data=decision_record,
                    decision_rationale=decision_record.get('decision_rationale', ''),
                    hash_chain=current_hash,
                    previous_hash=previous_hash,
                    compliance_flags={'article_53': True},
                    retention_until=datetime.now(UTC) + timedelta(days=365 * self.retention_years)
                )
                
                self.db_session.add(audit_event)
                self.db_session.commit()
                logged = True
                check_result = 'passed'
                evidence_ref = f"truth-audit-session:{session_id}"
            except Exception:
                check_result = 'failed'
                error_code = 'PERSISTENCE_FAILED'
                logger.exception(
                    "Control-map decision-log write failed",
                    extra={
                        "event": "truth_control_evidence.decision_log_failed",
                        "error_code": error_code,
                    },
                )
        
        return {
            'logged': logged,
            'result': check_result,
            'claim_type': 'automated_control_check',
            'check_version': 'truth-decision-log.v1',
            'scope': 'local_truth_gateway_request',
            'evidence_ref': evidence_ref,
            'source_record': f"truth-request:{session_id or 'not_available'}",
            'error_code': error_code,
            'record_hash': self._hash_query(str(decision_record)),
            'retention_years': self.retention_years
        }

    def _enforce_article_13(self, request: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Enforce Article 13: User explainability.
        
        Ensure users can understand AI decisions.
        """
        explainability_url = f"/api/truth/memory/explain/{session_id}" if session_id else None
        result = 'passed' if explainability_url else 'not_measured'
        
        return {
            'result': result,
            'claim_type': 'automated_control_check',
            'check_version': 'truth-explainability-link.v1',
            'scope': 'local_truth_gateway_request',
            'evidence_ref': explainability_url or 'not_available',
            'source_record': f"truth-request:{session_id or 'not_available'}",
            'explainability_url': explainability_url,
            'available_review_surfaces': [
                'reasoning_trace',
                'confidence_scores',
                'source_citations',
                'persona_contributions'
            ]
        }

    def _check_pii(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Check for PII in request."""
        query = request.get('query', '')
        pii_found = {}
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, query)
            if matches:
                pii_found[pii_type] = len(matches)
        
        return {
            'pii_found': bool(pii_found),
            'pii_types': list(pii_found.keys()),
            'pii_counts': pii_found,
            'result': 'failed' if pii_found else 'passed',
            'claim_type': 'automated_control_check',
            'check_version': 'truth-pii-pattern-check.v1',
            'scope': 'request_query',
            'evidence_ref': 'in_memory_pattern_check',
            'source_record': f"query-sha256:{self._hash_query(query)}",
        }

    def _hash_query(self, query: str) -> str:
        """Hash query for logging without storing raw content."""
        import hashlib
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def get_compliance_report(self, tenant_id: str = None,
                              date_from: datetime = None) -> Dict[str, Any]:
        """Generate a non-certifying control-map evidence availability report."""
        date_from = date_from or (datetime.now(UTC) - timedelta(days=30))
        
        report = {
            'schema_version': 'dle.truth-control-evidence-report.v1',
            'report_classification': 'self_assessment_evidence',
            'framework_map_is_certification': False,
            'generated_at': datetime.now(UTC).isoformat(),
            'period_start': date_from.isoformat(),
            'tenant_id': tenant_id,
            'framework_maps': self.COMPLIANCE_STANDARDS,
            'summary': {
                'overall_result': 'not_measured',
                'evidence_record_count': 0,
                'pass_rate': None,
            },
            'certification_claim': False,
            'limitations': [
                'Framework names organize technical control evidence only.',
                'No organizational controls or legal compliance conclusion are assessed.',
            ],
        }
        
        return report

    def get_audit_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full audit trail for session."""
        if not self.db_session:
            return []
        
        try:
            from models import TruthAuditEvent
            events = self.db_session.query(TruthAuditEvent).filter_by(
                session_id=session_id
            ).order_by(TruthAuditEvent.timestamp).all()
            
            return [event.to_dict() for event in events]
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []
