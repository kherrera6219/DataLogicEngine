"""
TruthGate Policy Evaluator

Defines and evaluates security policies.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    RATE_LIMIT = "rate_limit"
    DOWNGRADE = "downgrade"
    AUDIT = "audit"


@dataclass
class Policy:
    name: str
    description: str
    conditions: Dict[str, Any]
    action: PolicyAction
    priority: int = 0
    enabled: bool = True


class PolicyEvaluator:
    """
    Evaluates security policies for requests.
    
    Supports:
    - Rate limiting policies
    - Budget policies
    - Content policies
    - Compliance policies
    """
    
    DEFAULT_POLICIES = [
        Policy(
            name="rate_limit_default",
            description="Default rate limiting",
            conditions={"requests_per_minute": 60},
            action=PolicyAction.RATE_LIMIT,
            priority=100
        ),
        Policy(
            name="budget_enforcement",
            description="Enforce tenant budget limits",
            conditions={"budget_utilization_threshold": 0.95},
            action=PolicyAction.DENY,
            priority=90
        ),
        Policy(
            name="adversarial_block",
            description="Block adversarial inputs",
            conditions={"adversarial_score_threshold": 0.7},
            action=PolicyAction.DENY,
            priority=80
        ),
        Policy(
            name="compliance_audit",
            description="Audit all high-stakes requests",
            conditions={"tiers": ["high_stakes", "extreme", "autonomous"]},
            action=PolicyAction.AUDIT,
            priority=70
        )
    ]

    def __init__(self, custom_policies: List[Policy] = None):
        """Initialize with optional custom policies."""
        self.policies = sorted(
            self.DEFAULT_POLICIES + (custom_policies or []),
            key=lambda p: p.priority,
            reverse=True
        )

    def evaluate(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate all policies against request."""
        context = context or {}
        
        result = {
            'allowed': True,
            'policies_evaluated': [],
            'actions_triggered': [],
            'audit_required': False
        }
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            policy_result = self._evaluate_policy(policy, request, context)
            result['policies_evaluated'].append({
                'name': policy.name,
                'matched': policy_result['matched'],
                'action': policy.action.value if policy_result['matched'] else None
            })
            
            if policy_result['matched']:
                result['actions_triggered'].append(policy.action.value)
                
                if policy.action == PolicyAction.DENY:
                    result['allowed'] = False
                    result['deny_reason'] = policy.name
                
                if policy.action == PolicyAction.AUDIT:
                    result['audit_required'] = True
        
        return result

    def _evaluate_policy(self, policy: Policy, request: Dict[str, Any], 
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate single policy."""
        conditions = policy.conditions
        
        if 'tiers' in conditions:
            tier = request.get('tier', context.get('tier', 'trivial'))
            if tier in conditions['tiers']:
                return {'matched': True, 'reason': f"Tier {tier} matches policy"}
        
        if 'budget_utilization_threshold' in conditions:
            utilization = context.get('budget_utilization', 0)
            threshold = conditions['budget_utilization_threshold']
            if utilization >= threshold:
                return {'matched': True, 'reason': f"Budget utilization {utilization} >= {threshold}"}
        
        if 'adversarial_score_threshold' in conditions:
            score = context.get('adversarial_score', 0)
            threshold = conditions['adversarial_score_threshold']
            if score >= threshold:
                return {'matched': True, 'reason': f"Adversarial score {score} >= {threshold}"}
        
        return {'matched': False}

    def add_policy(self, policy: Policy) -> None:
        """Add a new policy."""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def get_policies(self) -> List[Dict[str, Any]]:
        """Get all policies as dictionaries."""
        return [
            {
                'name': p.name,
                'description': p.description,
                'action': p.action.value,
                'priority': p.priority,
                'enabled': p.enabled
            }
            for p in self.policies
        ]
