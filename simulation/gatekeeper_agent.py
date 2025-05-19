"""
Gatekeeper Agent

This module provides the Gatekeeper Agent for the UKG/USKD multi-layer simulation engine.
It controls access to simulation layers based on confidence scores, entropy values,
role conflicts, and regulatory triggers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class GatekeeperAgent:
    """
    Gatekeeper Agent
    
    Controls access to simulation Layers 4-10 based on data complexity, uncertainty, 
    entropy, or ethical triggers. Evaluates output from Layers 1-3 to decide whether
    to escalate simulation processing.
    
    The Gatekeeper Agent determines which layers to activate based on confidence scores,
    entropy values, role conflicts, and regulatory triggers. It acts as the central
    controller for the layered simulation architecture.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Gatekeeper Agent.
        
        Args:
            config (dict, optional): Configuration dictionary with thresholds
        """
        self.config = config or {}
        
        # Default thresholds
        self.confidence_threshold = self.config.get('confidence_threshold', 0.995)
        self.entropy_threshold = self.config.get('entropy_threshold', 0.75)
        self.role_conflict_threshold = self.config.get('role_conflict_threshold', 0.80)
        self.regulatory_threshold = self.config.get('regulatory_threshold', 0.85)
        
        # Layer activation thresholds (confidence scores below these trigger activation)
        self.layer_thresholds = {
            4: self.config.get('layer_4_threshold', 0.95),  # POV Engine
            5: self.config.get('layer_5_threshold', 0.90),  # Agent Simulation System
            6: self.config.get('layer_6_threshold', 0.85),  # Neural Logic Reconstructor
            7: self.config.get('layer_7_threshold', 0.80),  # Simulated AGI Core
            8: self.config.get('layer_8_threshold', 0.75),  # Quantum Fidelity Layer
            9: self.config.get('layer_9_threshold', 0.70),  # Recursive Planning Engine
            10: self.config.get('layer_10_threshold', 0.65),  # Emergence Detector
        }
        
        # Layer activation triggers (specific conditions that trigger layer activation)
        self.layer_triggers = {
            4: ["multirole", "viewpoint_plurality"],  # POV Engine Triggers
            5: ["knowledge_gap", "role_conflict"],    # Agent Simulation System Triggers
            6: ["low_cohesion", "belief_drift"],      # Neural Logic Reconstructor Triggers
            7: ["recursive_contradiction", "causal_failure"],  # Simulated AGI Core Triggers
            8: ["trust_entropy", "identity_inconsistency"],    # Quantum Fidelity Layer Triggers
            9: ["convergence_failure", "confidence_oscillation"],  # Recursive Planning Engine Triggers
            10: ["cross_agent_instability", "hallucination_drift"]  # Emergence Detector Triggers
        }
        
        # Decision log
        self.decision_log = []
        
        # Current decision
        self.current_decision = {}
        
        logging.info(f"[{datetime.now()}] GatekeeperAgent initialized with confidence threshold {self.confidence_threshold}")
    
    def evaluate(self, context: Dict) -> Dict:
        """
        Evaluate output from Layers 1-3 and determine which higher layers to activate.
        
        Args:
            context: Context dictionary with simulation results and metrics
                Required keys:
                - confidence_score: float (0.0-1.0)
                - entropy_score: float (0.0-1.0)
                Optional keys:
                - roles_triggered: list of role flags
                - regulatory_flags: list of regulatory flags
                - simulation_id: string identifier
                - simulation_pass: current pass number
                
        Returns:
            dict: Activation decisions for layers 4-10
        """
        # Extract metrics from context
        confidence = context.get('confidence_score', 0.0)
        entropy = context.get('entropy_score', 0.0)
        roles_triggered = set(context.get('roles_triggered', []))
        regulatory_flags = set(context.get('regulatory_flags', []))
        simulation_id = context.get('simulation_id', f"SIM_{datetime.now().timestamp()}")
        simulation_pass = context.get('simulation_pass', 1)
        
        # Initialize decision dictionary
        decision = {
            'timestamp': datetime.now().isoformat(),
            'simulation_id': simulation_id,
            'simulation_pass': simulation_pass,
            'layer_activations': {},
            'halt_due_to_entropy': entropy > self.entropy_threshold,
            'metrics': {
                'confidence': confidence,
                'entropy': entropy,
                'roles_triggered': list(roles_triggered),
                'regulatory_flags': list(regulatory_flags)
            }
        }
        
        # Determine layer activations based on confidence thresholds
        for layer in range(4, 11):
            layer_key = f"layer_{layer}"
            
            # Default activation based on confidence threshold
            activate = confidence < self.layer_thresholds[layer]
            
            # Check for specific triggers for this layer
            layer_specific_triggers = self.layer_triggers[layer]
            trigger_activated = False
            triggered_by = []
            
            for trigger in layer_specific_triggers:
                if trigger in roles_triggered or trigger in regulatory_flags:
                    trigger_activated = True
                    triggered_by.append(trigger)
            
            # Special logic for specific layers
            if layer == 4:  # POV Engine
                # Activate if multiple viewpoints detected
                pov_activate = "multirole" in roles_triggered or "viewpoint_plurality" in roles_triggered
                activate = activate or pov_activate
                if pov_activate:
                    triggered_by = ["Multiple viewpoints detected"]
            
            elif layer == 5:  # Integration Engine
                # Enhanced activation logic for Layer 5
                # Activate on knowledge gaps, role conflicts, or uncertainty indicators
                l5_activate = "knowledge_gap" in roles_triggered or "role_conflict" in roles_triggered
                
                # New triggers specific to Layer 5 Integration Engine
                integration_triggers = ["uncertainty", "validation_needed", "inconsistency"]
                for trigger in integration_triggers:
                    if trigger in roles_triggered or trigger in regulatory_flags:
                        l5_activate = True
                        if trigger not in triggered_by:
                            triggered_by.append(trigger)
                
                # Check uncertainty level for additional Layer 5 activation
                uncertainty_level = context.get("uncertainty_level", 0.0)
                if uncertainty_level > 0.3:  # Moderate uncertainty triggers Layer 5
                    l5_activate = True
                    if "high_uncertainty" not in triggered_by:
                        triggered_by.append("high_uncertainty")
                
                activate = activate or l5_activate
                if l5_activate and not triggered_by:
                    triggered_by = ["Knowledge gaps, role conflicts, or integration needs detected"]
                    
            elif layer == 7:  # Simulated AGI System
                # Enhanced activation logic for Layer 7
                # Activate on recursive contradictions, causal failures, or emergence indicators
                l7_activate = (
                    "recursive_contradiction" in roles_triggered or 
                    "causal_failure" in roles_triggered or
                    "emergence_indicator" in roles_triggered
                )
                
                # New triggers specific to Layer 7 AGI Simulation Engine
                agi_triggers = [
                    "goal_conflict", 
                    "belief_misalignment", 
                    "recursive_reasoning",
                    "confidence_decay",
                    "entropy_spike"
                ]
                for trigger in agi_triggers:
                    if trigger in roles_triggered or trigger in regulatory_flags:
                        l7_activate = True
                        if trigger not in triggered_by:
                            triggered_by.append(trigger)
                
                # Check confidence decay and entropy for additional Layer 7 activation
                confidence_history = context.get("historical_confidence", [])
                current_confidence = context.get("confidence_score", 0.0)
                
                # Calculate confidence decay if history exists
                if confidence_history and len(confidence_history) > 1:
                    # Look for significant confidence drop between passes
                    confidence_decay = max(0, max(confidence_history) - current_confidence)
                    if confidence_decay > 0.15:  # Significant decay triggers Layer 7
                        l7_activate = True
                        if "confidence_decay" not in triggered_by:
                            triggered_by.append("confidence_decay")
                
                # Check entropy level for additional Layer 7 activation
                entropy_level = context.get("entropy_score", 0.0)
                if entropy_level > 0.4:  # High entropy triggers Layer 7
                    l7_activate = True
                    if "high_entropy" not in triggered_by:
                        triggered_by.append("high_entropy")
                
                # Activate when multiple simulation passes have not improved confidence
                simulation_pass = context.get("simulation_pass", 1)
                if simulation_pass > 2 and current_confidence < 0.85:
                    l7_activate = True
                    if "multiple_passes_low_confidence" not in triggered_by:
                        triggered_by.append("multiple_passes_low_confidence")
                
                activate = activate or l7_activate
                if l7_activate and not triggered_by:
                    triggered_by = ["Recursive contradictions, goal conflicts, or agent belief misalignments detected"]
            
            elif layer == 8:  # Quantum Fidelity Layer
                # Activate on high entropy or trust issues
                qf_activate = entropy > 0.65 or "trust_entropy" in roles_triggered
                activate = activate or qf_activate
                if qf_activate and not triggered_by:
                    triggered_by = ["High entropy or trust issues detected"]
            
            elif layer == 10:  # Emergence Detector
                # Activate on very low confidence or special emergence flags
                emergence_activate = confidence < 0.60 or "emergence" in regulatory_flags
                activate = activate or emergence_activate
                if emergence_activate and not triggered_by:
                    triggered_by = ["Very low confidence or emergence indicators"]
            
            # Record decision for this layer
            decision['layer_activations'][layer_key] = {
                'activate': activate,
                'confidence_based': confidence < self.layer_thresholds[layer],
                'trigger_based': trigger_activated,
                'triggered_by': triggered_by
            }
        
        # Log decision
        self.decision_log.append({
            'context': context,
            'decision': decision
        })
        
        # Update current decision
        self.current_decision = decision
        
        logging.info(f"[{datetime.now()}] GatekeeperAgent evaluated simulation {simulation_id}, pass {simulation_pass}")
        
        return decision
    
    def get_active_layers(self) -> List[int]:
        """
        Get list of currently active layers.
        
        Returns:
            list: List of active layer numbers
        """
        active_layers = []
        
        if not self.current_decision:
            return active_layers
        
        layer_activations = self.current_decision.get('layer_activations', {})
        
        for layer_key, activation in layer_activations.items():
            if activation.get('activate', False):
                try:
                    layer_num = int(layer_key.split('_')[1])
                    active_layers.append(layer_num)
                except (ValueError, IndexError):
                    pass
        
        return sorted(active_layers)
    
    def should_halt(self) -> bool:
        """
        Check if simulation should halt based on current decision.
        
        Returns:
            bool: True if simulation should halt
        """
        if not self.current_decision:
            return False
        
        return self.current_decision.get('halt_due_to_entropy', False)
    
    def get_decision_log(self, limit: int = None) -> List[Dict]:
        """
        Get log of past decisions.
        
        Args:
            limit: Optional limit on number of log entries to return
            
        Returns:
            list: List of decision log entries
        """
        if limit is None:
            return self.decision_log
        
        return self.decision_log[-limit:]
    
    def reset(self) -> None:
        """
        Reset the Gatekeeper Agent state.
        """
        self.decision_log = []
        self.current_decision = {}
        logging.info(f"[{datetime.now()}] GatekeeperAgent reset")
    
    def check_layer_conditions(self, context: Dict, layer: int) -> Dict:
        """
        Check specific conditions for activating a single layer.
        
        Args:
            context: Context dictionary with simulation results and metrics
            layer: Layer number to check
            
        Returns:
            dict: Layer activation decision with reasons
        """
        if layer < 4 or layer > 10:
            return {
                'activate': False,
                'reason': "Layer number out of range (must be 4-10)"
            }
        
        # Evaluate full context
        self.evaluate(context)
        
        # Extract layer-specific decision
        layer_key = f"layer_{layer}"
        layer_decision = self.current_decision.get('layer_activations', {}).get(layer_key, {})
        
        return layer_decision
        
    def get_layer5_integration_parameters(self, context: Dict) -> Dict:
        """
        Get specific parameters for Layer 5 Integration Engine.
        
        This method extracts and configures parameters specifically for the
        Layer 5 Integration Engine based on the current context and decision state.
        
        Args:
            context: Context dictionary with simulation results and metrics
            
        Returns:
            dict: Configuration parameters for Layer 5 Integration Engine
        """
        # First ensure we've evaluated the context
        if not self.current_decision or context != self.decision_log[-1]['context'] if self.decision_log else True:
            self.evaluate(context)
            
        # Check if Layer 5 should be activated
        layer5_active = False
        layer5_decision = self.current_decision.get('layer_activations', {}).get('layer_5', {})
        if layer5_decision.get('activate', False):
            layer5_active = True
            
        # Default parameters for Layer 5
        integration_params = {
            'active': layer5_active,
            'uncertainty_threshold': 0.15,  # Default uncertainty threshold
            'verification_cycles': max(1, min(3, context.get('simulation_pass', 1))),  # Scale with pass number
            'refinement_depth': 2,
            'triggers': layer5_decision.get('triggered_by', []),
            'context_metrics': {
                'uncertainty': context.get('uncertainty_level', 0.0),
                'confidence': context.get('confidence_score', 0.0),
                'entropy': context.get('entropy_score', 0.0)
            }
        }
        
        # Customize based on context
        if context.get('high_priority', False):
            # Increase verification for high priority queries
            integration_params['verification_cycles'] += 1
            integration_params['refinement_depth'] += 1
            
        # Adjust for entropy
        if context.get('entropy_score', 0.0) > 0.5:
            integration_params['uncertainty_threshold'] = 0.1  # More strict for high entropy
            
        return integration_params
        
    def get_layer7_agi_parameters(self, context: Dict) -> Dict:
        """
        Get specific parameters for Layer 7 AGI Simulation Engine.
        
        This method extracts and configures parameters specifically for the
        Layer 7 AGI Simulation Engine based on the current context and decision state.
        
        Args:
            context: Context dictionary with simulation results and metrics
            
        Returns:
            dict: Configuration parameters for Layer 7 AGI Simulation Engine
        """
        # First ensure we've evaluated the context
        if not self.current_decision or context != self.decision_log[-1]['context'] if self.decision_log else True:
            self.evaluate(context)
            
        # Check if Layer 7 should be activated
        layer7_active = False
        layer7_decision = self.current_decision.get('layer_activations', {}).get('layer_7', {})
        if layer7_decision.get('activate', False):
            layer7_active = True
            
        # Get confidence history for decay calculations
        confidence_history = context.get("historical_confidence", [])
        current_confidence = context.get("confidence_score", 0.0)
        
        # Calculate confidence decay if history exists
        confidence_decay = 0.0
        if confidence_history and len(confidence_history) > 1:
            confidence_decay = max(0, max(confidence_history) - current_confidence)
        
        # Default parameters for Layer 7
        agi_params = {
            'active': layer7_active,
            'goal_expansion_depth': 3,  # Default recursion depth for goal expansion
            'belief_realignment_threshold': 0.2,  # Threshold for belief realignment
            'conflict_resolution_iterations': 5,  # Number of iterations for conflict resolution
            'goal_convergence_threshold': 0.75,  # Threshold for goal convergence
            'triggers': layer7_decision.get('triggered_by', []),
            'context_metrics': {
                'confidence': current_confidence,
                'confidence_decay': confidence_decay,
                'entropy': context.get('entropy_score', 0.0),
                'simulation_pass': context.get('simulation_pass', 1)
            }
        }
        
        # Customize based on context
        if context.get('high_priority', False) or context.get('critical', False):
            # Deeper goal expansion and more conflict resolution for high priority
            agi_params['goal_expansion_depth'] = 4
            agi_params['conflict_resolution_iterations'] = 7
            
        # Adjust for high entropy
        entropy_level = context.get('entropy_score', 0.0)
        if entropy_level > 0.5:
            # More strict convergence for high entropy
            agi_params['goal_convergence_threshold'] = 0.85
            
        # Adjust for multiple passes
        simulation_pass = context.get('simulation_pass', 1)
        if simulation_pass > 2:
            # Lower threshold for belief realignment in later passes
            # to allow more flexibility in restructuring beliefs
            agi_params['belief_realignment_threshold'] = max(0.1, 0.2 - (simulation_pass - 2) * 0.05)
            
        # Add POV expansion settings if POV engine is active
        if 4 in self.get_active_layers():
            agi_params['pov_expansion'] = True
            agi_params['viewpoint_count'] = context.get('viewpoint_count', 3)
            
        return agi_params