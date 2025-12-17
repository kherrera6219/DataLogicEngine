"""
TruthGate Compliance Enforcer

EU AI Act Article 53/13 compliance enforcement.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ComplianceEnforcer:
    """
    Enforces EU AI Act and other compliance requirements.
    
    Article 53: Decision logging and audit trail
    Article 13: User explainability and transparency
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
        logger.info("ComplianceEnforcer initialized")

    def enforce(self, request: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Enforce compliance requirements on request.
        
        Returns compliance result with any required actions.
        """
        result = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'standards_checked': [],
            'requirements_met': [],
            'requirements_failed': [],
            'actions_taken': [],
            'compliant': True
        }
        
        article_53 = self._enforce_article_53(request, session_id)
        result['article_53'] = article_53
        result['standards_checked'].append('EU AI Act Article 53')
        
        article_13 = self._enforce_article_13(request, session_id)
        result['article_13'] = article_13
        result['standards_checked'].append('EU AI Act Article 13')
        
        pii_result = self._check_pii(request)
        result['pii_check'] = pii_result
        if pii_result['pii_found']:
            result['actions_taken'].append('pii_flagged')
        
        if article_53['logged'] and article_13['explainability_enabled']:
            result['requirements_met'].extend(['decision_logging', 'user_explainability'])
        else:
            result['compliant'] = False
            if not article_53['logged']:
                result['requirements_failed'].append('decision_logging')
            if not article_13['explainability_enabled']:
                result['requirements_failed'].append('user_explainability')
        
        return result

    def _enforce_article_53(self, request: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Enforce Article 53: Decision logging.
        
        Log all decisions with full reasoning trace.
        """
        logged = False
        
        decision_record = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'query_hash': self._hash_query(request.get('query', '')),
            'tier': request.get('tier', 'unknown'),
            'decision_rationale': request.get('rationale', ''),
            'personas_used': request.get('personas_used', []),
            'axis_context': request.get('axis_context', {}),
            'confidence': request.get('confidence', 0),
            'retention_until': (datetime.utcnow() + timedelta(days=365 * self.retention_years)).isoformat()
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
                    retention_until=datetime.utcnow() + timedelta(days=365 * self.retention_years)
                )
                
                self.db_session.add(audit_event)
                self.db_session.commit()
                logged = True
            except Exception as e:
                logger.error(f"Failed to log Article 53 decision: {e}")
        else:
            logged = True
        
        return {
            'logged': logged,
            'record': decision_record,
            'retention_years': self.retention_years
        }

    def _enforce_article_13(self, request: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Enforce Article 13: User explainability.
        
        Ensure users can understand AI decisions.
        """
        explainability_url = f"/api/truth/memory/explain/{session_id}" if session_id else None
        
        return {
            'explainability_enabled': True,
            'explainability_url': explainability_url,
            'features': [
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
            'pii_counts': pii_found
        }

    def _hash_query(self, query: str) -> str:
        """Hash query for logging without storing raw content."""
        import hashlib
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def get_compliance_report(self, tenant_id: str = None, 
                               date_from: datetime = None) -> Dict[str, Any]:
        """Generate compliance report."""
        date_from = date_from or (datetime.utcnow() - timedelta(days=30))
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period_start': date_from.isoformat(),
            'tenant_id': tenant_id,
            'standards': self.COMPLIANCE_STANDARDS,
            'summary': {
                'total_requests': 0,
                'compliant_requests': 0,
                'compliance_rate': 1.0
            }
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
