"""
KA-44: Entropy Detection and Rewind

This algorithm detects emerging entropy and anomalies in simulation states,
identifying safe rollback points when simulations diverge into instability.
"""

import logging
from typing import Dict, List, Any, Optional
import time
import re

logger = logging.getLogger(__name__)

class EntropyDetectionAndRewind:
    """
    KA-44: Detects entropy and identifies rewind points for simulations.
    
    This algorithm monitors simulation states for signs of increasing entropy
    or anomalous behavior, providing safe rollback points when needed.
    """
    
    def __init__(self):
        """Initialize the Entropy Detection and Rewind system."""
        self.anomaly_patterns = self._initialize_anomaly_patterns()
        self.entropy_indicators = self._initialize_entropy_indicators()
        logger.info("KA-44: Entropy Detection and Rewind initialized")
    
    def _initialize_anomaly_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns that indicate anomalous simulation states."""
        return {
            "circular_reasoning": {
                "description": "Repeated statements that don't advance the reasoning",
                "patterns": [
                    r"loop\s+detected",
                    r"circular\s+reference",
                    r"repeated\s+statement",
                    r"infinite\s+recursion"
                ],
                "severity": "high"
            },
            "contradiction": {
                "description": "Logically contradictory statements",
                "patterns": [
                    r"contradiction\s+detected",
                    r"logical\s+inconsistency",
                    r"mutually\s+exclusive",
                    r"cannot\s+both\s+be\s+true"
                ],
                "severity": "high"
            },
            "divergence": {
                "description": "Simulation diverging from expected parameters",
                "patterns": [
                    r"divergence\s+detected",
                    r"unexpected\s+pathway",
                    r"parameter\s+violation",
                    r"boundary\s+exceeded"
                ],
                "severity": "medium"
            },
            "hallucination": {
                "description": "Generating non-existent information",
                "patterns": [
                    r"hallucination\s+detected",
                    r"fabricated\s+information",
                    r"non-existent\s+reference",
                    r"imaginary\s+data"
                ],
                "severity": "medium"
            },
            "error_cascade": {
                "description": "Cascading errors from initial mistake",
                "patterns": [
                    r"error\s+cascade",
                    r"propagating\s+error",
                    r"compounding\s+mistake",
                    r"error\s+amplification"
                ],
                "severity": "high"
            }
        }
    
    def _initialize_entropy_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize indicators for measuring simulation entropy."""
        return {
            "complexity_increase": {
                "description": "Rapid increase in reasoning complexity",
                "metrics": ["step_length", "branching_factor", "nesting_depth"],
                "threshold": 2.5,  # Multiplier from baseline
                "severity": "medium"
            },
            "confidence_decrease": {
                "description": "Significant drop in confidence levels",
                "metrics": ["confidence_score", "certainty_level", "probability_estimate"],
                "threshold": 0.4,  # Absolute decrease
                "severity": "high"
            },
            "coherence_loss": {
                "description": "Decreasing coherence between simulation steps",
                "metrics": ["narrative_coherence", "logical_connection", "semantic_similarity"],
                "threshold": 0.5,  # Absolute decrease
                "severity": "high"
            },
            "randomness_increase": {
                "description": "Increasing randomness in simulation outputs",
                "metrics": ["entropy_score", "predictability", "pattern_detection"],
                "threshold": 0.3,  # Absolute increase
                "severity": "medium"
            },
            "resource_explosion": {
                "description": "Exponential increase in resource consumption",
                "metrics": ["memory_usage", "computation_time", "token_count"],
                "threshold": 3.0,  # Multiplier from baseline
                "severity": "critical"
            }
        }
    
    def analyze_simulation(self, simulation_snapshots: List[str],
                         metrics: Optional[List[Dict[str, Any]]] = None,
                         rewind_depth: int = 3) -> Dict[str, Any]:
        """
        Analyze simulation for entropy and anomalies.
        
        Args:
            simulation_snapshots: List of simulation state descriptions
            metrics: Optional list of metric dictionaries for each snapshot
            rewind_depth: How far back to rewind when anomaly detected
            
        Returns:
            Dictionary with analysis results
        """
        # Validate inputs
        if not simulation_snapshots:
            return {
                "anomaly_detected": False,
                "entropy_level": 0.0,
                "rewind_required": False,
                "rewind_point": None,
                "snapshot_count": 0
            }
        
        # Ensure metrics list matches snapshots if provided
        if metrics is not None and len(metrics) != len(simulation_snapshots):
            # Truncate or extend metrics to match snapshots
            if len(metrics) > len(simulation_snapshots):
                metrics = metrics[:len(simulation_snapshots)]
            else:
                default_metric = {"confidence": 0.8, "complexity": 1.0}
                metrics.extend([default_metric] * (len(simulation_snapshots) - len(metrics)))
        elif metrics is None:
            # Create default metrics
            metrics = [{"confidence": 0.8, "complexity": 1.0}] * len(simulation_snapshots)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(simulation_snapshots)
        
        # Measure entropy
        entropy_levels = self._measure_entropy(simulation_snapshots, metrics)
        
        # Determine if rewind is required
        rewind_required = False
        rewind_point = None
        rewind_reason = None
        
        # Initialize rewind index
        rewind_index = 0
        
        # Check for anomalies that require rewind
        for i, snapshot_anomalies in enumerate(anomalies):
            if snapshot_anomalies:
                high_severity_anomalies = [a for a in snapshot_anomalies if a["severity"] in ["high", "critical"]]
                if high_severity_anomalies:
                    rewind_required = True
                    rewind_reason = f"High severity anomaly detected: {high_severity_anomalies[0]['type']}"
                    rewind_index = i
                    break
        
        # Check for entropy thresholds that require rewind
        for i, entropy in enumerate(entropy_levels):
            if entropy > 0.7:  # High entropy threshold
                if not rewind_required:  # Don't override anomaly rewind
                    rewind_required = True
                    rewind_reason = f"High entropy level detected: {entropy:.2f}"
                    rewind_index = i
                break
        
        # Determine rewind point if needed
        if rewind_required:
            safe_index = max(0, rewind_index - rewind_depth)
            rewind_point = {
                "index": safe_index,
                "snapshot": simulation_snapshots[safe_index],
                "reason": rewind_reason
            }
        
        # Calculate final entropy level
        final_entropy = max(entropy_levels) if entropy_levels else 0.0
        
        # Prepare result
        result = {
            "anomaly_detected": any(anomalies),
            "entropy_level": final_entropy,
            "rewind_required": rewind_required,
            "rewind_point": rewind_point,
            "snapshot_count": len(simulation_snapshots),
            "anomalies": anomalies,
            "entropy_levels": entropy_levels,
            "safe_snapshots": [i for i, a in enumerate(anomalies) if not a]
        }
        
        return result
    
    def _detect_anomalies(self, snapshots: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Detect anomalies in simulation snapshots.
        
        Args:
            snapshots: List of simulation state descriptions
            
        Returns:
            List of lists of anomaly dictionaries for each snapshot
        """
        anomalies = []
        
        for snapshot in snapshots:
            snapshot_anomalies = []
            snapshot_lower = snapshot.lower()
            
            # Check for anomaly patterns
            for anomaly_type, anomaly_info in self.anomaly_patterns.items():
                for pattern in anomaly_info["patterns"]:
                    if re.search(pattern, snapshot_lower):
                        # Record anomaly
                        anomaly = {
                            "type": anomaly_type,
                            "description": anomaly_info["description"],
                            "severity": anomaly_info["severity"],
                            "pattern_matched": pattern
                        }
                        
                        snapshot_anomalies.append(anomaly)
                        break  # Only record one instance of each anomaly type
            
            anomalies.append(snapshot_anomalies)
        
        return anomalies
    
    def _measure_entropy(self, snapshots: List[str], 
                      metrics: List[Dict[str, Any]]) -> List[float]:
        """
        Measure entropy levels in simulation snapshots.
        
        Args:
            snapshots: List of simulation state descriptions
            metrics: List of metric dictionaries for each snapshot
            
        Returns:
            List of entropy levels for each snapshot
        """
        entropy_levels = []
        
        # Calculate baseline metrics from first few snapshots
        baseline_count = min(3, len(snapshots))
        if baseline_count == 0:
            return []
        
        baseline_metrics = {}
        for key in metrics[0].keys():
            baseline_metrics[key] = sum(metrics[i].get(key, 0) for i in range(baseline_count)) / baseline_count
        
        # Calculate entropy for each snapshot
        for i, (snapshot, metric) in enumerate(zip(snapshots, metrics)):
            # Initialize entropy components
            complexity_factor = 0.0
            confidence_factor = 0.0
            length_factor = 0.0
            randomness_factor = 0.0
            
            # Calculate complexity factor
            if "complexity" in metric and "complexity" in baseline_metrics:
                baseline = max(0.001, baseline_metrics["complexity"])
                current = metric["complexity"]
                ratio = current / baseline
                complexity_factor = min(1.0, max(0.0, (ratio - 1) / 5))  # Normalize to 0-1
            
            # Calculate confidence factor
            if "confidence" in metric and "confidence" in baseline_metrics:
                baseline = max(0.001, baseline_metrics["confidence"])
                current = metric["confidence"]
                confidence_factor = min(1.0, max(0.0, (baseline - current) / baseline))
            
            # Calculate length factor (longer snapshots might indicate increasing complexity)
            baseline_length = sum(len(snapshots[i]) for i in range(baseline_count)) / baseline_count
            current_length = len(snapshot)
            length_ratio = current_length / max(1, baseline_length)
            length_factor = min(1.0, max(0.0, (length_ratio - 1) / 3))
            
            # Calculate randomness factor (more randomness = higher entropy)
            if i > 0:
                # Simple measure: lack of common substrings between consecutive snapshots
                prev_snapshot = snapshots[i-1]
                common_substrings = self._count_common_substrings(prev_snapshot, snapshot)
                max_possible = min(len(prev_snapshot), len(snapshot)) / 5  # Rough estimate
                commonality = common_substrings / max(1, max_possible)
                randomness_factor = min(1.0, max(0.0, 1.0 - commonality))
            
            # Calculate overall entropy
            # Weighted combination of factors
            entropy = (
                0.3 * complexity_factor +
                0.3 * confidence_factor +
                0.2 * length_factor +
                0.2 * randomness_factor
            )
            
            entropy_levels.append(round(entropy, 4))
        
        return entropy_levels
    
    def _count_common_substrings(self, str1: str, str2: str, min_length: int = 5) -> int:
        """
        Count common substrings between two strings.
        
        Args:
            str1: First string
            str2: Second string
            min_length: Minimum substring length to count
            
        Returns:
            Count of common substrings
        """
        # Simple approximation using sliding window
        count = 0
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        for i in range(len(str1_lower) - min_length + 1):
            substring = str1_lower[i:i+min_length]
            if substring in str2_lower:
                count += 1
        
        return count
    
    def get_safe_rollback_state(self, simulation_snapshots: List[str],
                             anomaly_detected: bool = False,
                             entropy_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Get a safe state to roll back to when issues are detected.
        
        Args:
            simulation_snapshots: List of simulation state descriptions
            anomaly_detected: Whether an anomaly was explicitly detected
            entropy_threshold: Entropy threshold for determining safety
            
        Returns:
            Dictionary with safe rollback state
        """
        if not simulation_snapshots:
            return {
                "error": "No simulation snapshots provided",
                "success": False
            }
        
        # If no issues detected and explicitly stated, no rewind needed
        if not anomaly_detected:
            return {
                "rewind_needed": False,
                "safe_state": "no rewind needed",
                "message": "No anomalies detected, continuing simulation"
            }
        
        # If only one snapshot, use it
        if len(simulation_snapshots) == 1:
            return {
                "rewind_needed": True,
                "safe_state": simulation_snapshots[0],
                "index": 0,
                "message": "Only one snapshot available, using it as safe state"
            }
        
        # Default to the initial state
        safe_state = simulation_snapshots[0]
        safe_index = 0
        
        # For more complex implementations, would analyze entropy levels
        # For this simpler version, we'll use the earliest state that doesn't
        # have obvious anomaly markers
        for i, snapshot in enumerate(simulation_snapshots):
            snapshot_lower = snapshot.lower()
            
            # Check for obvious anomaly markers
            if "anomaly" not in snapshot_lower and "error" not in snapshot_lower:
                if i > 0:  # If not the first snapshot, this is a good candidate
                    safe_state = snapshot
                    safe_index = i
                    break
        
        return {
            "rewind_needed": True,
            "safe_state": safe_state,
            "index": safe_index,
            "message": f"Rewinding to safe state at index {safe_index}"
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Entropy Detection and Rewind (KA-44) on the provided data.
    
    Args:
        data: A dictionary containing simulation snapshots to analyze
        
    Returns:
        Dictionary with entropy analysis and rewind information
    """
    simulation_snapshots = data.get("simulation_snapshots", [])
    metrics = data.get("metrics")
    rewind_depth = data.get("rewind_depth", 3)
    anomaly_detected = data.get("anomaly_detected", False)
    
    # For simple cases with anomaly flag but no metrics
    if simulation_snapshots and anomaly_detected and metrics is None:
        detector = EntropyDetectionAndRewind()
        result = detector.get_safe_rollback_state(simulation_snapshots, anomaly_detected)
        
        if "error" in result:
            return {
                "algorithm": "KA-44",
                "error": result["error"],
                "success": False
            }
        
        return {
            "algorithm": "KA-44",
            "rewind_point": result["safe_state"],
            "rewind_needed": result["rewind_needed"],
            "timestamp": time.time(),
            "success": True
        }
    
    # For more detailed analysis
    detector = EntropyDetectionAndRewind()
    result = detector.analyze_simulation(simulation_snapshots, metrics, rewind_depth)
    
    return {
        "algorithm": "KA-44",
        "rewind_point": result["rewind_point"]["snapshot"] if result["rewind_point"] else "no rewind needed",
        "entropy_level": result["entropy_level"],
        "anomaly_detected": result["anomaly_detected"],
        "timestamp": time.time(),
        "success": True
    }