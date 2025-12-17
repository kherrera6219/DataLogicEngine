"""
TruthCore Tier Management

Defines the 5-tier workflow system and tier selection logic.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WorkflowTier(Enum):
    """Workflow tier enumeration with priority levels."""
    TRIVIAL = ('trivial', 0, 1)
    MODERATE = ('moderate', 1, 3)
    HIGH_STAKES = ('high_stakes', 2, 10)
    EXTREME = ('extreme', 3, 60)
    AUTONOMOUS = ('autonomous', 4, 300)
    HITL = ('hitl', 5, 30)
    
    def __init__(self, tier_name: str, priority: int, sla_seconds: int):
        self.tier_name = tier_name
        self.priority = priority
        self.sla_seconds = sla_seconds


@dataclass
class TierConfig:
    """Configuration for a workflow tier."""
    name: str
    priority: int
    sla_seconds: int
    description: str
    max_tokens: int
    temperature: float
    requires_validation: bool
    requires_simulation: bool
    requires_human_review: bool


class TierManager:
    """
    Manages workflow tier selection and configuration.
    
    Integrates with TruthGate for budget-aware tier downgrade.
    """
    
    DEFAULT_CONFIGS = {
        'trivial': TierConfig(
            name='trivial',
            priority=0,
            sla_seconds=1,
            description='Direct Answer',
            max_tokens=1000,
            temperature=0.0,
            requires_validation=False,
            requires_simulation=False,
            requires_human_review=False
        ),
        'moderate': TierConfig(
            name='moderate',
            priority=1,
            sla_seconds=3,
            description='Hybrid Vector RAG + CoT',
            max_tokens=4000,
            temperature=0.3,
            requires_validation=True,
            requires_simulation=False,
            requires_human_review=False
        ),
        'high_stakes': TierConfig(
            name='high_stakes',
            priority=2,
            sla_seconds=10,
            description='12-Step Refinement Workflow',
            max_tokens=8000,
            temperature=0.2,
            requires_validation=True,
            requires_simulation=False,
            requires_human_review=False
        ),
        'extreme': TierConfig(
            name='extreme',
            priority=3,
            sla_seconds=60,
            description='GNN/NN/Quantum Simulations',
            max_tokens=16000,
            temperature=0.1,
            requires_validation=True,
            requires_simulation=True,
            requires_human_review=False
        ),
        'autonomous': TierConfig(
            name='autonomous',
            priority=4,
            sla_seconds=300,
            description='Governed Multi-Agent',
            max_tokens=32000,
            temperature=0.4,
            requires_validation=True,
            requires_simulation=True,
            requires_human_review=True
        )
    }

    def __init__(self, custom_configs: Dict[str, TierConfig] = None):
        """Initialize with optional custom configurations."""
        self.configs = {**self.DEFAULT_CONFIGS}
        if custom_configs:
            self.configs.update(custom_configs)

    def get_tier_config(self, tier: str) -> Optional[TierConfig]:
        """Get configuration for a specific tier."""
        return self.configs.get(tier)

    def select_tier(self, query: str, context: Dict[str, Any] = None, 
                    budget_remaining: float = None) -> str:
        """
        Select appropriate tier based on query and constraints.
        
        Considers:
        - Query complexity
        - Domain sensitivity
        - Budget constraints
        - Context requirements
        """
        context = context or {}
        
        if context.get('force_tier'):
            forced = context['force_tier']
            if forced in self.configs:
                return forced
        
        base_tier = self._analyze_query_complexity(query, context)
        
        if budget_remaining is not None:
            base_tier = self._apply_budget_constraint(base_tier, budget_remaining)
        
        return base_tier

    def _analyze_query_complexity(self, query: str, context: Dict[str, Any]) -> str:
        """Analyze query to determine base tier."""
        query_lower = query.lower()
        query_length = len(query)
        
        autonomous_indicators = ['create a complete', 'build an application', 
                                  'develop a system', 'implement full']
        extreme_indicators = ['simulate', 'model', 'predict', 'quantum']
        high_stakes_indicators = ['legal', 'medical', 'financial', 'regulatory',
                                   'compliance', 'critical', 'security']
        moderate_indicators = ['analyze', 'compare', 'explain', 'evaluate', 
                               'synthesize', 'research']
        
        if any(ind in query_lower for ind in autonomous_indicators):
            return 'autonomous'
        
        if any(ind in query_lower for ind in extreme_indicators):
            return 'extreme'
        
        if any(ind in query_lower for ind in high_stakes_indicators):
            return 'high_stakes'
        
        if any(ind in query_lower for ind in moderate_indicators) or query_length > 500:
            return 'moderate'
        
        return 'trivial'

    def _apply_budget_constraint(self, tier: str, budget_remaining: float) -> str:
        """Downgrade tier if budget is insufficient."""
        tier_costs = {
            'trivial': 0.01,
            'moderate': 0.05,
            'high_stakes': 0.20,
            'extreme': 1.00,
            'autonomous': 5.00
        }
        
        tier_priority = ['trivial', 'moderate', 'high_stakes', 'extreme', 'autonomous']
        current_idx = tier_priority.index(tier) if tier in tier_priority else 0
        
        while current_idx > 0:
            cost = tier_costs.get(tier_priority[current_idx], 0)
            if cost <= budget_remaining:
                break
            current_idx -= 1
            logger.warning(f"Budget constraint: Downgrading from {tier} to {tier_priority[current_idx]}")
        
        return tier_priority[current_idx]

    def get_tier_priority_queue_name(self, tier: str) -> str:
        """Get priority queue name for tier."""
        priority_map = {
            'trivial': 'p0',
            'moderate': 'p1',
            'high_stakes': 'p2',
            'extreme': 'p3',
            'autonomous': 'p4',
            'hitl': 'p5'
        }
        return priority_map.get(tier, 'p1')
