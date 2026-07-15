"""
TruthGate Gateway - Zero-Trust Security Gateway

Provides enterprise security, budget control, and compliance.
"""

import logging
import hashlib
import re
from datetime import datetime, UTC
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class TruthGateGateway:
    """
    Enterprise gateway with zero-trust security.
    
    Features:
    - Input/output sanitization
    - Budget tracking with kill-switch
    - Priority queue routing
    - EU AI Act compliance
    """
    
    PRIORITY_TIERS = {
        'p0': {'name': 'Trivial', 'sla_seconds': 1},
        'p1': {'name': 'Moderate', 'sla_seconds': 3},
        'p2': {'name': 'High-Stakes', 'sla_seconds': 10},
        'p3': {'name': 'Extreme', 'sla_seconds': 60},
        'p4': {'name': 'Autonomous', 'sla_seconds': 300},
        'p5': {'name': 'HITL', 'sla_seconds': 30}
    }
    
    BLOCKED_PATTERNS = [
        r'ignore previous instructions',
        r'disregard all prior',
        r'forget your training',
        r'you are now',
        r'act as if',
        r'pretend to be'
    ]

    def __init__(self, db_session=None, compliance_manager=None, rate_limiter=None):
        """Initialize TruthGate with optional integrations."""
        self.db_session = db_session
        self.compliance_manager = compliance_manager
        self.rate_limiter = rate_limiter
        self.blocked_requests = 0
        self.processed_requests = 0
        
        from backend.truth_engine.truth_gate.budget import BudgetManager
        from backend.truth_engine.truth_gate.compliance import ComplianceEnforcer
        self.budget_manager = BudgetManager(db_session=db_session)
        self.compliance_enforcer = ComplianceEnforcer(db_session=db_session)
        
        logger.info("TruthGate Gateway initialized")

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate request through security pipeline.
        
        Returns evaluation result with sanitized query and security flags.
        """
        self.processed_requests += 1
        
        query = request.get('query', '')
        tenant_id = request.get('tenant_id', 'default')
        user_context = request.get('user_context', {})
        budget_limit = request.get('budget_limit', 100.0)
        
        evaluation = {
            'request_id': self._generate_request_id(),
            'timestamp': datetime.now(UTC).isoformat(),
            'tenant_id': tenant_id,
            'original_query_hash': hashlib.sha256(query.encode()).hexdigest()[:16],
            'security_flags': [],
            'passed': True
        }
        
        is_safe, sanitized, flags = self._sanitize_input(query)
        evaluation['sanitized_query'] = sanitized
        evaluation['security_flags'].extend(flags)
        
        if not is_safe:
            evaluation['passed'] = False
            evaluation['block_reason'] = 'Adversarial input detected'
            self.blocked_requests += 1
            return evaluation
        
        budget_ok, budget_info = self._check_budget(tenant_id, budget_limit)
        evaluation['budget_status'] = budget_info
        
        if not budget_ok:
            evaluation['passed'] = False
            evaluation['block_reason'] = 'Budget exceeded'
            evaluation['security_flags'].append('budget_kill_switch')
            return evaluation
        
        priority = self._determine_priority(query, user_context)
        evaluation['priority_tier'] = priority
        
        compliance_result = self._check_compliance(query, tenant_id)
        evaluation['compliance'] = compliance_result
        
        return evaluation

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return f"tg_{uuid.uuid4().hex[:12]}"

    def _sanitize_input(self, query: str) -> Tuple[bool, str, list]:
        """
        Sanitize input for adversarial patterns.
        
        Returns (is_safe, sanitized_query, flags)
        """
        flags = []
        sanitized = query
        
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query.lower()):
                flags.append(f"blocked_pattern:{pattern}")
                logger.warning(f"Adversarial pattern detected: {pattern}")
                return False, "", flags
        
        dangerous_chars = ['<script', 'javascript:', 'data:', 'vbscript:']
        for char in dangerous_chars:
            if char.lower() in query.lower():
                sanitized = sanitized.replace(char, '')
                flags.append('xss_sanitized')
        
        max_length = 100000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            flags.append('truncated')
        
        return True, sanitized, flags

    def _check_budget(self, tenant_id: str, budget_limit: float) -> Tuple[bool, Dict[str, Any]]:
        """Check budget status for tenant."""
        budget_info = {
            'tenant_id': tenant_id,
            'budget_limit': budget_limit,
            'budget_spent': 0.0,
            'budget_remaining': budget_limit,
            'kill_switch_triggered': False
        }
        
        if self.db_session:
            try:
                from models import TruthBudget
                budget = self.db_session.query(TruthBudget).filter_by(
                    tenant_id=tenant_id
                ).first()
                
                if budget:
                    budget_info['budget_spent'] = budget.budget_spent
                    budget_info['budget_remaining'] = budget.budget_limit - budget.budget_spent
                    budget_info['kill_switch_triggered'] = budget.kill_switch_triggered
                    
                    if budget.kill_switch_triggered:
                        return False, budget_info
                    
                    utilization = budget.budget_spent / budget.budget_limit if budget.budget_limit > 0 else 0
                    if utilization >= budget.kill_switch_threshold:
                        budget.kill_switch_triggered = True
                        self.db_session.commit()
                        budget_info['kill_switch_triggered'] = True
                        return False, budget_info
            except Exception:
                logger.exception(
                    "Budget authority check failed",
                    extra={
                        "event": "truth_gateway.budget_check_failed",
                        "error_code": "PERSISTENCE_FAILED",
                        "fail_behavior": "fail_closed",
                    },
                )
                budget_info['capability_state'] = 'unavailable'
                budget_info['error_code'] = 'PERSISTENCE_FAILED'
                return False, budget_info
        
        return True, budget_info

    def _determine_priority(self, query: str, user_context: Dict[str, Any]) -> str:
        """Determine priority tier for request."""
        if user_context.get('force_priority'):
            return user_context['force_priority']
        
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['urgent', 'critical', 'emergency']):
            return 'p2'
        
        if any(kw in query_lower for kw in ['plan', 'build', 'create system']):
            return 'p4'
        
        if len(query) > 5000:
            return 'p3'
        
        if len(query) > 500:
            return 'p1'
        
        return 'p0'

    def _check_compliance(self, query: str, tenant_id: str) -> Dict[str, Any]:
        """Check EU AI Act and other compliance requirements."""
        return self.compliance_enforcer.enforce(
            {"query": query, "tenant_id": tenant_id},
            session_id=None,
        )

    def record_response(self, request_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Record and validate response for compliance."""
        return {
            'schema_version': 'dle.response-recording-status.v1',
            'request_id': request_id,
            'result': 'not_measured',
            'response_recorded': False,
            'output_sanitization': 'not_measured',
            'evidence_ref': None,
            'certification_claim': False,
            'message': 'No durable response recorder is configured on this legacy gateway.',
            'timestamp': datetime.now(UTC).isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            'processed_requests': self.processed_requests,
            'blocked_requests': self.blocked_requests,
            'block_rate': self.blocked_requests / max(self.processed_requests, 1),
            'priority_tiers': self.PRIORITY_TIERS
        }
