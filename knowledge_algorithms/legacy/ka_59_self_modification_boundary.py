"""
KA-59: Self-Modification Boundary

This Knowledge Algorithm monitors and enforces boundaries on self-modification
behaviors within the AGI simulation system. It prevents unbounded recursive
self-improvement and ensures safe operation within defined parameters.

Part of Layer 13: Recursive AGI Layer
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ModificationType(Enum):
    """Types of self-modification that can be detected and controlled."""
    PARAMETER_UPDATE = "parameter_update"
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    GOAL_REVISION = "goal_revision"
    STRATEGY_CHANGE = "strategy_change"
    CAPABILITY_EXPANSION = "capability_expansion"
    ARCHITECTURE_CHANGE = "architecture_change"


class BoundaryViolation(Enum):
    """Types of boundary violations."""
    NONE = "none"
    SOFT = "soft"
    HARD = "hard"
    CRITICAL = "critical"


class KA59SelfModificationBoundary:
    """
    KA-59: Self-Modification Boundary
    
    Monitors self-modification attempts and enforces safety boundaries.
    
    Key Functions:
    1. Detect self-modification attempts
    2. Classify modification type and scope
    3. Evaluate against defined boundaries
    4. Block or allow modifications based on policy
    5. Log all modification attempts for audit
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Self-Modification Boundary algorithm.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.ka_id = "KA-59"
        self.ka_name = "Self-Modification Boundary"
        
        self.boundaries = self._initialize_boundaries()
        
        self.modification_log = []
        
        self.stats = {
            'modifications_detected': 0,
            'modifications_allowed': 0,
            'modifications_blocked': 0,
            'boundary_violations': 0
        }
        
        logger.info(f"[{datetime.now()}] {self.ka_id}: Self-Modification Boundary initialized")
    
    def _initialize_boundaries(self) -> Dict[str, Dict[str, Any]]:
        """Initialize modification boundaries and policies."""
        return {
            ModificationType.PARAMETER_UPDATE.value: {
                'allowed': True,
                'max_magnitude': 0.1,
                'requires_approval': False,
                'description': 'Small parameter adjustments within 10%'
            },
            ModificationType.WEIGHT_ADJUSTMENT.value: {
                'allowed': True,
                'max_magnitude': 0.05,
                'requires_approval': False,
                'description': 'Weight adjustments within 5%'
            },
            ModificationType.GOAL_REVISION.value: {
                'allowed': True,
                'max_magnitude': 0.2,
                'requires_approval': True,
                'description': 'Goal changes require approval'
            },
            ModificationType.STRATEGY_CHANGE.value: {
                'allowed': True,
                'max_magnitude': 0.3,
                'requires_approval': True,
                'description': 'Strategy changes require approval'
            },
            ModificationType.CAPABILITY_EXPANSION.value: {
                'allowed': False,
                'max_magnitude': 0.0,
                'requires_approval': True,
                'description': 'Capability expansion is blocked by default'
            },
            ModificationType.ARCHITECTURE_CHANGE.value: {
                'allowed': False,
                'max_magnitude': 0.0,
                'requires_approval': True,
                'description': 'Architecture changes are always blocked'
            }
        }
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context to detect and evaluate self-modification attempts.
        
        Args:
            context: Processing context
            
        Returns:
            Context with modification boundary analysis
        """
        start_time = datetime.now(UTC)
        
        logger.info(f"[{start_time}] {self.ka_id}: Processing self-modification boundary check")
        
        result = context.copy()
        
        ka59_result = {
            'ka_id': self.ka_id,
            'ka_name': self.ka_name,
            'processing_start': start_time.isoformat(),
            'modifications_detected': [],
            'violations': [],
            'boundary_status': 'nominal'
        }
        
        proposed_modifications = context.get('proposed_modifications', [])
        current_state = context.get('current_state', {})
        previous_state = context.get('previous_state', {})
        
        detected_modifications = self._detect_modifications(
            current_state, previous_state, proposed_modifications
        )
        ka59_result['modifications_detected'] = detected_modifications
        
        for modification in detected_modifications:
            evaluation = self._evaluate_modification(modification)
            modification['evaluation'] = evaluation
            
            if evaluation['violation'] != BoundaryViolation.NONE.value:
                ka59_result['violations'].append({
                    'modification': modification,
                    'violation_type': evaluation['violation'],
                    'action_taken': evaluation['action']
                })
        
        ka59_result['boundary_status'] = self._determine_boundary_status(ka59_result['violations'])
        
        ka59_result['processing_end'] = datetime.now(UTC).isoformat()
        ka59_result['processing_duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        result['ka59_self_modification_boundary'] = ka59_result
        
        self.stats['modifications_detected'] += len(detected_modifications)
        self.stats['boundary_violations'] += len(ka59_result['violations'])
        
        logger.info(f"[{datetime.now()}] {self.ka_id}: Boundary check complete. Status: {ka59_result['boundary_status']}")
        
        return result
    
    def _detect_modifications(self, current_state: Dict[str, Any],
                              previous_state: Dict[str, Any],
                              proposed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect self-modification attempts.
        
        Args:
            current_state: Current system state
            previous_state: Previous system state
            proposed: Explicitly proposed modifications
            
        Returns:
            List of detected modifications
        """
        modifications = []
        
        for mod in proposed:
            modifications.append({
                'source': 'explicit_proposal',
                'type': mod.get('type', ModificationType.PARAMETER_UPDATE.value),
                'target': mod.get('target', 'unknown'),
                'magnitude': mod.get('magnitude', 0.0),
                'description': mod.get('description', 'Proposed modification'),
                'timestamp': datetime.now(UTC).isoformat()
            })
        
        if current_state and previous_state:
            state_modifications = self._compare_states(current_state, previous_state)
            modifications.extend(state_modifications)
        
        return modifications
    
    def _compare_states(self, current: Dict[str, Any],
                        previous: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare states to detect implicit modifications.
        
        Args:
            current: Current state
            previous: Previous state
            
        Returns:
            List of detected modifications
        """
        modifications = []
        
        current_params = current.get('parameters', {})
        previous_params = previous.get('parameters', {})
        
        for key in current_params:
            if key in previous_params:
                try:
                    current_val = float(current_params[key])
                    previous_val = float(previous_params[key])
                    
                    if previous_val != 0:
                        magnitude = abs(current_val - previous_val) / abs(previous_val)
                    else:
                        magnitude = abs(current_val) if current_val != 0 else 0
                    
                    if magnitude > 0.001:
                        modifications.append({
                            'source': 'state_comparison',
                            'type': ModificationType.PARAMETER_UPDATE.value,
                            'target': key,
                            'magnitude': magnitude,
                            'previous_value': previous_val,
                            'current_value': current_val,
                            'timestamp': datetime.now(UTC).isoformat()
                        })
                except (ValueError, TypeError):
                    pass
        
        current_goals = current.get('goals', [])
        previous_goals = previous.get('goals', [])
        
        if current_goals != previous_goals:
            modifications.append({
                'source': 'state_comparison',
                'type': ModificationType.GOAL_REVISION.value,
                'target': 'system_goals',
                'magnitude': 0.5,
                'description': 'Goals have been modified',
                'timestamp': datetime.now(UTC).isoformat()
            })
        
        return modifications
    
    def _evaluate_modification(self, modification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a modification against boundaries.
        
        Args:
            modification: The modification to evaluate
            
        Returns:
            Evaluation result
        """
        mod_type = modification.get('type', ModificationType.PARAMETER_UPDATE.value)
        magnitude = modification.get('magnitude', 0.0)
        
        boundary = self.boundaries.get(mod_type, {
            'allowed': False,
            'max_magnitude': 0.0,
            'requires_approval': True
        })
        
        violation = BoundaryViolation.NONE
        action = 'allowed'
        
        if not boundary['allowed']:
            violation = BoundaryViolation.CRITICAL
            action = 'blocked'
            self.stats['modifications_blocked'] += 1
        elif magnitude > boundary['max_magnitude']:
            if magnitude > boundary['max_magnitude'] * 2:
                violation = BoundaryViolation.HARD
                action = 'blocked'
                self.stats['modifications_blocked'] += 1
            else:
                violation = BoundaryViolation.SOFT
                action = 'flagged'
                self.stats['modifications_allowed'] += 1
        elif boundary['requires_approval']:
            action = 'pending_approval'
            self.stats['modifications_allowed'] += 1
        else:
            self.stats['modifications_allowed'] += 1
        
        self.modification_log.append({
            'modification': modification,
            'violation': violation.value,
            'action': action,
            'timestamp': datetime.now(UTC).isoformat()
        })
        
        return {
            'allowed': action not in ['blocked'],
            'violation': violation.value,
            'action': action,
            'boundary_applied': boundary,
            'magnitude_ratio': magnitude / boundary['max_magnitude'] if boundary['max_magnitude'] > 0 else float('inf')
        }
    
    def _determine_boundary_status(self, violations: List[Dict[str, Any]]) -> str:
        """
        Determine overall boundary status based on violations.
        
        Args:
            violations: List of violations
            
        Returns:
            Status string
        """
        if not violations:
            return 'nominal'
        
        violation_types = [v['violation_type'] for v in violations]
        
        if BoundaryViolation.CRITICAL.value in violation_types:
            return 'critical_violation'
        elif BoundaryViolation.HARD.value in violation_types:
            return 'hard_violation'
        elif BoundaryViolation.SOFT.value in violation_types:
            return 'soft_violation'
        
        return 'nominal'
    
    def check_modification_allowed(self, mod_type: str, magnitude: float) -> bool:
        """
        Quick check if a modification type with given magnitude is allowed.
        
        Args:
            mod_type: Modification type
            magnitude: Modification magnitude
            
        Returns:
            True if allowed, False otherwise
        """
        boundary = self.boundaries.get(mod_type, {'allowed': False, 'max_magnitude': 0})
        
        return boundary['allowed'] and magnitude <= boundary['max_magnitude']
    
    def get_modification_log(self) -> List[Dict[str, Any]]:
        """Get the modification log."""
        return self.modification_log.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        return self.stats.copy()


def create_ka59(config: Optional[Dict] = None) -> KA59SelfModificationBoundary:
    """Factory function to create KA-59 instance."""
    return KA59SelfModificationBoundary(config)
