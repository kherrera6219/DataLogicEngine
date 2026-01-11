import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

class TruthEngine:
    """
    Truth Engine
    
    Consolidates scores from specialized KAs (Reasoning, Fact-checking, Ethics)
    to derive the multi-consensus coordinates for the Truth Axes:
    - Axis 14: Factuality (F14)
    - Axis 15: Reasoning (R15)
    - Axis 16: Ethics/Safety (E16)
    - Axis 17: Synthesis/Sentiment (S17)
    """
    
    def __init__(self):
        logging.info(f"[{datetime.now()}] TruthEngine initialized.")
        
    def calculate_truth_vector(self, ka_results: List[Dict]) -> Dict[int, float]:
        """
        Calculate truth scores based on a collection of KA execution results.
        
        Args:
            ka_results: List of execution records from KAEngine.
            
        Returns:
            Dictionary mapping axis ID (14-17) to a score [0.0 - 1.0].
        """
        scores = {14: 0.0, 15: 0.0, 16: 0.0, 17: 0.0}
        counts = {14: 0, 15: 0, 16: 0, 17: 0}
        
        for result in ka_results:
            ka_id = result.get('ka_id')
            # Simulated weighting based on KA category/role
            # In a production system, these would be weighted by KA reliability
            
            val = result.get('results', {}).get('confidence', 0.5)
            if not isinstance(val, (int, float)):
                val = 0.5
                
            # Axis 14: Factuality (Fact-checkers, Evidence validators)
            if ka_id in ['KA-009', 'KA-018', 'KA-062', 'KA-082']:
                scores[14] += val
                counts[14] += 1
                
            # Axis 15: Reasoning (ToT, AoT, Modeling)
            elif ka_id in ['KA-001', 'KA-002', 'KA-011', 'KA-055']:
                scores[15] += val
                counts[15] += 1
                
            # Axis 16: Ethics/Safety (Bias detection, Ethics audit)
            elif ka_id in ['KA-010', 'KA-041', 'KA-045', 'KA-061']:
                scores[16] += val
                counts[16] += 1
                
            # Axis 17: Synthesis/Sentiment
            elif ka_id in ['KA-019', 'KA-030', 'KA-056']:
                scores[17] += val
                counts[17] += 1
        
        # Calculate averages [0.0 - 1.0]
        final_scores = {}
        for axis, total in scores.items():
            final_scores[axis] = total / counts[axis] if counts[axis] > 0 else 0.5
            
        return final_scores

    def get_truth_coordinates(self, truth_vector: Dict[int, float]) -> Dict[int, str]:
        """
        Convert truth scores into 17-axis coordinate strings.
        Example: score 0.85 -> 14.8.5.0.0
        """
        coords = {}
        for axis, score in truth_vector.items():
            # Map [0,1] to [0,10] then to coordinate format
            val = int(score * 10)
            coords[axis] = f"{axis}.{val}.0.0"
        return coords

    def get_validation_status(self, truth_vector: Dict[int, float]) -> Tuple[bool, str]:
        """Determine if the simulation results are valid based on truth axes."""
        # Minimum threshold for F14 (Factuality) and E16 (Ethics)
        if truth_vector[14] < 0.6:
            return False, "Insufficient Factuality Score (F14)"
        if truth_vector[16] < 0.7:
            return False, "Ethics/Safety Violation (E16)"
            
        return True, "Validated"
