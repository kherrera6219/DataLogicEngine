"""
TruthGate Budget Manager

Manages per-tenant budget tracking with kill-switch.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BudgetManager:
    """
    Manages budget allocation and tracking.
    
    Features:
    - Per-tenant budget limits
    - Automatic kill-switch at threshold
    - Tier-based cost estimation
    - Budget reset scheduling
    """
    
    TIER_COSTS = {
        'trivial': 0.001,
        'moderate': 0.01,
        'high_stakes': 0.05,
        'extreme': 0.25,
        'autonomous': 1.00
    }
    
    TOKEN_COST_PER_1K = 0.002

    def __init__(self, db_session=None, default_budget: float = 100.0):
        """Initialize budget manager."""
        self.db_session = db_session
        self.default_budget = default_budget
        self.in_memory_budgets = {}
        logger.info("BudgetManager initialized")

    def get_budget(self, tenant_id: str) -> Dict[str, Any]:
        """Get current budget status for tenant."""
        if self.db_session:
            try:
                from models import TruthBudget
                budget = self.db_session.query(TruthBudget).filter_by(
                    tenant_id=tenant_id
                ).first()
                
                if budget:
                    return budget.to_dict()
                else:
                    new_budget = TruthBudget(
                        tenant_id=tenant_id,
                        budget_limit=self.default_budget,
                        budget_spent=0.0,
                        kill_switch_threshold=0.95,
                        downgrade_tier='trivial',
                        tier_limits={'trivial': 1000, 'moderate': 500, 'high_stakes': 100}
                    )
                    self.db_session.add(new_budget)
                    self.db_session.commit()
                    logger.info(f"Created new budget for tenant {tenant_id}")
                    return new_budget.to_dict()
            except Exception as e:
                logger.error(f"Failed to get/create budget from DB: {e}")
                self.db_session.rollback()
        
        if tenant_id in self.in_memory_budgets:
            return self.in_memory_budgets[tenant_id]
        
        return self._create_default_budget(tenant_id)

    def _create_default_budget(self, tenant_id: str) -> Dict[str, Any]:
        """Create default budget for new tenant."""
        budget = {
            'tenant_id': tenant_id,
            'budget_limit': self.default_budget,
            'budget_spent': 0.0,
            'budget_remaining': self.default_budget,
            'budget_utilization': 0.0,
            'kill_switch_triggered': False,
            'kill_switch_threshold': 0.95,
            'downgrade_tier': 'trivial',
            'created_at': datetime.now(UTC).isoformat()
        }
        self.in_memory_budgets[tenant_id] = budget
        return budget

    def estimate_cost(self, tier: str, token_count: int = 0) -> float:
        """Estimate cost for a request."""
        base_cost = self.TIER_COSTS.get(tier, 0.01)
        token_cost = (token_count / 1000) * self.TOKEN_COST_PER_1K
        return base_cost + token_cost

    def charge(self, tenant_id: str, amount: float, tier: str = None,
               session_id: str = None) -> Dict[str, Any]:
        """Charge amount to tenant budget."""
        budget = self.get_budget(tenant_id)
        
        new_spent = budget['budget_spent'] + amount
        new_remaining = budget['budget_limit'] - new_spent
        utilization = new_spent / budget['budget_limit'] if budget['budget_limit'] > 0 else 1.0
        
        result = {
            'tenant_id': tenant_id,
            'amount_charged': amount,
            'previous_spent': budget['budget_spent'],
            'new_spent': new_spent,
            'remaining': new_remaining,
            'utilization': utilization,
            'kill_switch_triggered': False,
            'session_id': session_id,
            'tier': tier,
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        if utilization >= budget.get('kill_switch_threshold', 0.95):
            result['kill_switch_triggered'] = True
            result['downgrade_tier'] = budget.get('downgrade_tier', 'trivial')
            logger.warning(f"Kill switch triggered for tenant {tenant_id}")
        
        if self.db_session:
            try:
                from models import TruthBudget
                db_budget = self.db_session.query(TruthBudget).filter_by(
                    tenant_id=tenant_id
                ).first()
                
                if db_budget:
                    db_budget.budget_spent = new_spent
                    db_budget.kill_switch_triggered = result['kill_switch_triggered']
                    self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to update budget in DB: {e}")
        
        if tenant_id in self.in_memory_budgets:
            self.in_memory_budgets[tenant_id]['budget_spent'] = new_spent
            self.in_memory_budgets[tenant_id]['budget_remaining'] = new_remaining
            self.in_memory_budgets[tenant_id]['kill_switch_triggered'] = result['kill_switch_triggered']
        
        return result

    def reset_budget(self, tenant_id: str, new_limit: float = None) -> Dict[str, Any]:
        """Reset budget for tenant."""
        limit = new_limit or self.default_budget
        
        if self.db_session:
            try:
                from models import TruthBudget
                db_budget = self.db_session.query(TruthBudget).filter_by(
                    tenant_id=tenant_id
                ).first()
                
                if db_budget:
                    db_budget.budget_spent = 0.0
                    db_budget.budget_limit = limit
                    db_budget.kill_switch_triggered = False
                    db_budget.reset_at = datetime.now(UTC)
                    self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to reset budget in DB: {e}")
        
        if tenant_id in self.in_memory_budgets:
            self.in_memory_budgets[tenant_id] = self._create_default_budget(tenant_id)
            self.in_memory_budgets[tenant_id]['budget_limit'] = limit
        
        return self.get_budget(tenant_id)

    def check_can_proceed(self, tenant_id: str, tier: str, 
                          estimated_tokens: int = 1000) -> Dict[str, Any]:
        """Check if tenant can proceed with request."""
        budget = self.get_budget(tenant_id)
        estimated_cost = self.estimate_cost(tier, estimated_tokens)
        
        can_proceed = True
        recommended_tier = tier
        
        if budget['kill_switch_triggered']:
            can_proceed = False
            recommended_tier = budget.get('downgrade_tier', 'trivial')
        elif budget['budget_remaining'] < estimated_cost:
            can_proceed = False
            for fallback_tier in ['extreme', 'high_stakes', 'moderate', 'trivial']:
                fallback_cost = self.estimate_cost(fallback_tier, estimated_tokens)
                if budget['budget_remaining'] >= fallback_cost:
                    recommended_tier = fallback_tier
                    can_proceed = True
                    break
        
        return {
            'can_proceed': can_proceed,
            'requested_tier': tier,
            'recommended_tier': recommended_tier,
            'estimated_cost': estimated_cost,
            'budget_remaining': budget['budget_remaining'],
            'kill_switch_triggered': budget['kill_switch_triggered']
        }
