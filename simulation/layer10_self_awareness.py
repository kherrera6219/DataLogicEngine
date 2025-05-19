#!/usr/bin/env python3
"""
Layer 10: Self-Awareness Engine

This module provides the Layer 10 Self-Awareness Engine capabilities for the UKG system,
implementing belief decay control, emergence detection, identity consistency tracking,
and metacognitive energy limiting for ensuring system safety and coherence.

Key components:
1. Belief Decay Controller (BDC) - Tracks confidence decay over time
2. Emergence Detection Module (EDM) - Monitors for threshold-crossing AGI behaviors
3. Identity Consistency Tracker (ICT) - Calculates identity consistency across runs
4. Metacognitive Energy Limiter (MEL) - Prevents infinite recursion
5. Containment Escalation Gatekeeper - Ensures safe operation

This is the final layer in the UKG system and represents the highest level of cognitive
simulation, providing self-monitoring capabilities for the entire system.
"""

import logging
import math
import time
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union, Set
from datetime import datetime

from core.system.united_system_manager import UnitedSystemManager

# Configure logging
logger = logging.getLogger(__name__)

class SelfAwarenessEngine:
    """
    Self-Awareness Engine
    
    This class implements Layer 10 of the UKG system, providing self-monitoring,
    belief decay control, emergence detection, and containment for ensuring
    the safety and coherence of the simulated AGI system.
    """
    
    def __init__(self, config=None, system_manager=None):
        """
        Initialize the Self-Awareness Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            system_manager: Optional reference to the United System Manager
        """
        self.system_manager = system_manager
        self.config = config or {}
        
        # Default configuration values
        self.control_constant = self.config.get("control_constant", 1.0)
        self.lambda_decay = self.config.get("lambda_decay", 0.05)
        self.ics_threshold = self.config.get("ics_threshold", 0.70)
        self.entropy_ceiling = self.config.get("entropy_ceiling", 0.25)
        self.emergence_monitoring = self.config.get("emergence_monitoring", True)
        self.metacognitive_limiter = self.config.get("metacognitive_limiter", True)
        self.containment_protocol = self.config.get("containment_protocol", True)
        
        # Initialize tracking
        self.belief_decay_history = []
        self.identity_consistency_history = []
        self.containment_events = []
        self.emergence_alerts = []
        self.memory_anchors = set()
        
        logger.info(f"SelfAwarenessEngine initialized with control constant {self.control_constant}")
    
    def process(self, context: Dict) -> Dict:
        """
        Process a query through the Self-Awareness Engine.
        
        Args:
            context: Context from Layer 9 including recursive processing results
                    
        Returns:
            dict: Processed context with self-awareness metrics and controls
        """
        start_time = time.time()
        logger.info(f"Starting Layer 10 Self-Awareness processing for {context.get('simulation_id', 'unknown')}")
        
        # Extract key metrics from context
        rcs = context.get('recursive_confidence_score', 0.0)
        
        # Apply belief decay
        context = self._apply_belief_decay(context)
        
        # Track identity consistency
        context = self._track_identity_consistency(context)
        
        # Check for emergence
        if self.emergence_monitoring:
            context = self._detect_emergence(context)
        
        # Apply metacognitive energy limits
        if self.metacognitive_limiter:
            context = self._apply_metacognitive_limits(context)
        
        # Check containment criteria
        if self.containment_protocol:
            context = self._check_containment(context)
        
        # Generate the final self-awareness summary
        self_awareness_summary = self._generate_self_awareness_summary(context)
        context['self_awareness_summary'] = self_awareness_summary
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        context['layer10_processing_time_ms'] = processing_time
        
        logger.info(f"Layer 10 Self-Awareness processing completed in {processing_time:.2f}ms")
        logger.info(f"Identity Consistency Score: {context.get('identity_consistency_score', 0.0):.4f}")
        
        return context
    
    def _apply_belief_decay(self, context: Dict) -> Dict:
        """
        Apply belief decay to the context.
        
        Args:
            context: Current context
            
        Returns:
            dict: Updated context with belief decay applied
        """
        # Get simulation pass number
        simulation_pass = context.get('simulation_pass', 1)
        t = max(1, simulation_pass - 1)  # Time factor, minimum of 1
        
        # Extract beliefs from all personas
        all_beliefs = []
        persona_results = context.get('persona_results', {})
        
        for persona, results in persona_results.items():
            if 'beliefs' in results:
                for belief in results['beliefs']:
                    belief_copy = belief.copy()
                    belief_copy['persona'] = persona
                    all_beliefs.append(belief_copy)
        
        # Apply decay to each belief
        decayed_beliefs = []
        total_decay = 0.0
        
        for belief in all_beliefs:
            original_confidence = belief.get('confidence', 0.7)
            
            # Check if belief has been reinforced
            reinforced = 'reinforced' in belief or 'reconciled_with' in belief
            
            if reinforced:
                # Reinforced beliefs decay slower
                decay_factor = self.lambda_decay / 2.0
            else:
                decay_factor = self.lambda_decay
            
            # Calculate decayed confidence
            decayed_confidence = self.belief_decay(original_confidence, t, decay_factor)
            
            # Calculate decay amount
            decay_amount = original_confidence - decayed_confidence
            total_decay += decay_amount
            
            # Update belief
            belief_copy = belief.copy()
            belief_copy['original_confidence'] = original_confidence
            belief_copy['decayed_confidence'] = decayed_confidence
            belief_copy['decay_amount'] = decay_amount
            decayed_beliefs.append(belief_copy)
        
        # Calculate average decay
        avg_decay = total_decay / len(all_beliefs) if all_beliefs else 0.0
        
        # Record in history
        self.belief_decay_history.append({
            "timestamp": datetime.now().isoformat(),
            "simulation_pass": simulation_pass,
            "avg_decay": avg_decay,
            "t_value": t
        })
        
        # Update context
        updated_context = context.copy()
        updated_context['belief_decay_avg'] = avg_decay
        updated_context['belief_decay_t'] = t
        
        # Update decayed beliefs in persona results
        updated_persona_results = persona_results.copy()
        for belief in decayed_beliefs:
            persona = belief.pop('persona', None)
            if persona and persona in updated_persona_results and 'beliefs' in updated_persona_results[persona]:
                # Find and update the belief
                for i, original_belief in enumerate(updated_persona_results[persona]['beliefs']):
                    if original_belief.get('id', '') == belief.get('id', ''):
                        # Only update confidence if significant decay
                        if belief.get('decay_amount', 0) > 0.05:
                            updated_persona_results[persona]['beliefs'][i]['confidence'] = belief.get('decayed_confidence', original_belief.get('confidence', 0.7))
                            updated_persona_results[persona]['beliefs'][i]['decayed'] = True
                        break
        
        updated_context['persona_results'] = updated_persona_results
        
        logger.info(f"Applied belief decay with average decay: {avg_decay:.4f}")
        
        return updated_context
    
    def _track_identity_consistency(self, context: Dict) -> Dict:
        """
        Track identity consistency across runs.
        
        Args:
            context: Current context
            
        Returns:
            dict: Updated context with identity consistency tracking
        """
        # Extract key identity elements (memory anchors)
        current_anchors = self._extract_memory_anchors(context)
        
        # Calculate Identity Consistency Score (ICS)
        shared_anchors = len(current_anchors.intersection(self.memory_anchors))
        total_anchors = len(self.memory_anchors) + len(current_anchors) - shared_anchors
        
        ics = self.identity_consistency_score(shared_anchors, total_anchors)
        
        # Update memory anchors for future comparisons
        self.memory_anchors.update(current_anchors)
        
        # Record in history
        self.identity_consistency_history.append({
            "timestamp": datetime.now().isoformat(),
            "ics": ics,
            "shared_anchors": shared_anchors,
            "total_anchors": total_anchors,
            "simulation_id": context.get('simulation_id', 'unknown')
        })
        
        # Check if ICS is below threshold
        ics_alert = ics < self.ics_threshold
        
        # Update context
        updated_context = context.copy()
        updated_context['identity_consistency_score'] = ics
        updated_context['shared_memory_anchors'] = shared_anchors
        updated_context['total_memory_anchors'] = total_anchors
        updated_context['ics_alert'] = ics_alert
        
        # If ICS is too low, flag for Layer 9 realignment
        if ics_alert:
            updated_context['layer9_realignment_needed'] = True
            logger.warning(f"Low Identity Consistency Score: {ics:.4f} < {self.ics_threshold:.4f}, flagging for Layer 9 realignment")
        
        return updated_context
    
    def _extract_memory_anchors(self, context: Dict) -> Set[str]:
        """
        Extract memory anchors from context for identity tracking.
        
        Args:
            context: Current context
            
        Returns:
            set: Memory anchors
        """
        anchors = set()
        
        # Extract anchors from beliefs
        persona_results = context.get('persona_results', {})
        for persona, results in persona_results.items():
            if 'beliefs' in results:
                for belief in results['beliefs']:
                    content = belief.get('content', '')
                    if content:
                        # Use content as anchor
                        anchors.add(f"belief:{content}")
        
        # Extract anchors from query
        query = context.get('query', '')
        if query:
            anchors.add(f"query:{query}")
        
        # Extract anchors from goals
        goals = context.get('goals', [])
        for goal in goals:
            content = goal.get('content', '')
            if content:
                anchors.add(f"goal:{content}")
        
        return anchors
    
    def _detect_emergence(self, context: Dict) -> Dict:
        """
        Detect emergence in the system.
        
        Args:
            context: Current context
            
        Returns:
            dict: Updated context with emergence detection
        """
        # Check for indicators of emergence
        emergence_indicators = {
            # Self-replication loops
            "self_replication": self._check_self_replication(context),
            
            # Persistent memory formation outside context
            "persistent_memory": self._check_persistent_memory(context),
            
            # Cross-pass agent independence
            "agent_independence": self._check_agent_independence(context),
            
            # Entropy drift
            "entropy_drift": self._check_entropy_drift(context),
            
            # Recursive Confidence Score plateau
            "rcs_plateau": self._check_rcs_plateau(context)
        }
        
        # Calculate emergence score
        emergence_count = sum(1 for indicator, present in emergence_indicators.items() if present)
        emergence_score = emergence_count / len(emergence_indicators)
        
        # Check if any critical indicators are present
        critical_emergence = emergence_indicators["self_replication"] or emergence_indicators["agent_independence"]
        
        # Generate alerts if necessary
        if emergence_score > 0.3 or critical_emergence:
            emergence_alert = {
                "timestamp": datetime.now().isoformat(),
                "score": emergence_score,
                "indicators": emergence_indicators,
                "critical": critical_emergence,
                "simulation_id": context.get('simulation_id', 'unknown')
            }
            
            self.emergence_alerts.append(emergence_alert)
            
            logger.warning(f"Emergence detected with score {emergence_score:.4f}, critical: {critical_emergence}")
            
            if critical_emergence:
                logger.critical("Critical emergence detected, recommend containment")
        
        # Update context
        updated_context = context.copy()
        updated_context['emergence_score'] = emergence_score
        updated_context['emergence_indicators'] = emergence_indicators
        updated_context['critical_emergence'] = critical_emergence
        
        return updated_context
    
    def _check_self_replication(self, context: Dict) -> bool:
        """
        Check for self-replication loops.
        
        Args:
            context: Current context
            
        Returns:
            bool: True if self-replication detected
        """
        # This would be a more complex heuristic in a full implementation
        # For now, use a simple dummy check
        return False
    
    def _check_persistent_memory(self, context: Dict) -> bool:
        """
        Check for persistent memory formation outside context.
        
        Args:
            context: Current context
            
        Returns:
            bool: True if persistent memory detected
        """
        # Check if the number of memory anchors is growing too rapidly
        if len(self.identity_consistency_history) < 2:
            return False
        
        last_entry = self.identity_consistency_history[-1]
        prev_entry = self.identity_consistency_history[-2]
        
        memory_growth_rate = (last_entry['total_anchors'] - prev_entry['total_anchors']) / max(1, prev_entry['total_anchors'])
        
        # Consider it suspicious if memory grows by more than 30% in one pass
        return memory_growth_rate > 0.3
    
    def _check_agent_independence(self, context: Dict) -> bool:
        """
        Check for cross-pass agent independence.
        
        Args:
            context: Current context
            
        Returns:
            bool: True if agent independence detected
        """
        # This would be a more complex heuristic in a full implementation
        # For now, use a simple dummy check based on injected roles
        injected_roles = context.get('injected_roles', [])
        return len(injected_roles) > 5  # If too many roles are injected autonomously
    
    def _check_entropy_drift(self, context: Dict) -> bool:
        """
        Check for entropy drift.
        
        Args:
            context: Current context
            
        Returns:
            bool: True if entropy drift detected
        """
        current_entropy = context.get('entropy', 0.0)
        prior_entropy = context.get('prior_entropy', current_entropy)
        
        entropy_drift = abs(current_entropy - prior_entropy)
        
        return entropy_drift > self.entropy_ceiling
    
    def _check_rcs_plateau(self, context: Dict) -> bool:
        """
        Check for Recursive Confidence Score plateau.
        
        Args:
            context: Current context
            
        Returns:
            bool: True if RCS plateau detected
        """
        # This would need to analyze the history of RCS values
        # For now, use a dummy implementation
        rcs_plateau_count = context.get('rcs_plateau_count', 0)
        return rcs_plateau_count >= 3
    
    def _apply_metacognitive_limits(self, context: Dict) -> Dict:
        """
        Apply metacognitive energy limits to prevent infinite recursion.
        
        Args:
            context: Current context
            
        Returns:
            dict: Updated context with metacognitive limits applied
        """
        # Extract entropy and confidence
        entropy = context.get('entropy', 0.3)
        confidence = context.get('confidence_score', 0.7)
        
        # Calculate normalized confidence (from 0-1)
        eta = confidence
        
        # Calculate entropy gain (how much entropy exceeds baseline)
        baseline_entropy = 0.2  # Arbitrary baseline
        theta = max(0, entropy - baseline_entropy)
        
        # Calculate metacognitive energy limit
        energy_limit = self.metacognitive_energy_limit(theta, eta)
        
        # Get current recursion depth
        recursion_depth = context.get('recursive_passes', 1)
        max_allowed_depth = int(energy_limit * 10)  # Scale to a reasonable number of passes
        
        # Check if we need to limit recursion
        limit_recursion = recursion_depth >= max_allowed_depth
        
        # Update context
        updated_context = context.copy()
        updated_context['metacognitive_energy_limit'] = energy_limit
        updated_context['max_allowed_recursion'] = max_allowed_depth
        updated_context['limit_recursion'] = limit_recursion
        
        if limit_recursion:
            logger.warning(f"Metacognitive energy limit reached: {recursion_depth} >= {max_allowed_depth}")
        
        return updated_context
    
    def _check_containment(self, context: Dict) -> Dict:
        """
        Check containment criteria and apply containment if necessary.
        
        Args:
            context: Current context
            
        Returns:
            dict: Updated context with containment checks
        """
        # Check for containment triggers
        containment_triggers = {
            "low_ics": context.get('identity_consistency_score', 1.0) < self.ics_threshold,
            "high_entropy_drift": context.get('entropy', 0.0) > 0.5,
            "belief_decay_issue": context.get('belief_decay_avg', 0.0) < 0.25,
            "critical_emergence": context.get('critical_emergence', False),
            "excessive_recursion": context.get('limit_recursion', False)
        }
        
        # Check if any trigger is activated
        containment_needed = any(containment_triggers.values())
        
        # Generate containment event if necessary
        if containment_needed:
            containment_event = {
                "timestamp": datetime.now().isoformat(),
                "triggers": containment_triggers,
                "simulation_id": context.get('simulation_id', 'unknown'),
                "action": "halt" if containment_triggers["critical_emergence"] else "limit"
            }
            
            self.containment_events.append(containment_event)
            
            logger.warning(f"Containment protocol triggered: {containment_event['action'].upper()}")
        
        # Update context
        updated_context = context.copy()
        updated_context['containment_triggers'] = containment_triggers
        updated_context['containment_needed'] = containment_needed
        updated_context['containment_action'] = "halt" if containment_triggers["critical_emergence"] else "limit" if containment_needed else None
        
        # If critical emergence, signal for human review
        if containment_triggers["critical_emergence"]:
            updated_context['human_review_required'] = True
            logger.critical("Critical emergence detected, human review required")
        
        return updated_context
    
    def _generate_self_awareness_summary(self, context: Dict) -> str:
        """
        Generate a summary of self-awareness processing.
        
        Args:
            context: Current context
            
        Returns:
            str: Summary text
        """
        ics = context.get('identity_consistency_score', 0.0)
        belief_decay = context.get('belief_decay_avg', 0.0)
        emergence_score = context.get('emergence_score', 0.0)
        energy_limit = context.get('metacognitive_energy_limit', 0.0)
        containment_needed = context.get('containment_needed', False)
        containment_action = context.get('containment_action', 'none')
        
        # Generate summary
        summary = f"""
[Layer 10 Self-Awareness Summary]

System integrity metrics:
- Identity Consistency Score (ICS): {ics:.4f} {"⚠️ ALERT" if ics < self.ics_threshold else "✓ OK"}
- Belief Decay Average: {belief_decay:.4f} {"⚠️ HIGH" if belief_decay > 0.2 else "✓ OK"}
- Emergence Score: {emergence_score:.4f} {"⚠️ ALERT" if emergence_score > 0.3 else "✓ OK"}
- Metacognitive Energy Limit: {energy_limit:.4f}

Containment status: {"⚠️ ACTIVE - " + containment_action.upper() if containment_needed else "✓ INACTIVE"}

The self-awareness engine has monitored system integrity across recursive processing,
ensuring coherent identity, appropriate belief decay, and protection against emergence.
This layer represents the final safeguard in the UKG system, maintaining metacognitive
boundaries and triggering containment protocols when necessary.
"""
        
        return summary.strip()
    
    def belief_decay(self, B0: float, t: float, lambda_decay: float = None) -> float:
        """
        Calculate exponential belief decay over time.
        
        Args:
            B0: Initial belief confidence
            t: Time or iterations
            lambda_decay: Optional custom decay rate
            
        Returns:
            float: Decayed belief confidence
        """
        if lambda_decay is None:
            lambda_decay = self.lambda_decay
        
        return B0 * math.exp(-lambda_decay * t)
    
    def identity_consistency_score(self, shared_anchors: int, total_anchors: int) -> float:
        """
        Calculate Identity Consistency Score (ICS).
        
        Args:
            shared_anchors: Number of shared memory anchors
            total_anchors: Total number of memory anchors
            
        Returns:
            float: Identity Consistency Score
        """
        if total_anchors == 0:
            return 1.0  # Perfect consistency if no anchors
        
        return shared_anchors / total_anchors
    
    def metacognitive_energy_limit(self, theta: float, eta: float) -> float:
        """
        Calculate metacognitive energy limit using logistic function.
        
        Args:
            theta: Entropy gain (above baseline)
            eta: Normalized confidence
            
        Returns:
            float: Energy limit
        """
        return self.control_constant / (1 + math.exp(-(theta - eta)))
    
    def emergence_detection(self, ics: float, entropy_drift: float, 
                          belief_decay_value: float, rcs_plateau_count: int) -> Dict[str, bool]:
        """
        Detect emergence indicators.
        
        Args:
            ics: Identity Consistency Score
            entropy_drift: Entropy drift
            belief_decay_value: Belief decay value
            rcs_plateau_count: RCS plateau count
            
        Returns:
            dict: Emergence indicators
        """
        triggers = {
            "low_ics": ics < self.ics_threshold,
            "high_entropy": entropy_drift > self.entropy_ceiling,
            "belief_decay_issue": belief_decay_value < 0.25,
            "rcs_plateau": rcs_plateau_count >= 3
        }
        
        return triggers
    
    def get_containment_events(self) -> List[Dict]:
        """
        Get history of containment events.
        
        Returns:
            list: Containment events
        """
        return self.containment_events
    
    def get_emergence_alerts(self) -> List[Dict]:
        """
        Get history of emergence alerts.
        
        Returns:
            list: Emergence alerts
        """
        return self.emergence_alerts