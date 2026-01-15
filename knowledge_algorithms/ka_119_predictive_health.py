"""
KA-119: Predictive Health Monitor

This Knowledge Algorithm acts as an AIOps agent. It analyzes time-series metrics 
(simulated implementation uses simple linear projection) to predict system health issues 
like Token Budget Exhaustion or Latency Spikes before they impact users.

Input: Metric History (List[float])
Output: Health Prediction & Recommended Action
"""

from typing import Dict, Any, List
from .ka_master_controller import KnowledgeAlgorithm

class KA119PredictiveHealth(KnowledgeAlgorithm):
    """
    Predictive Anomaly Detection Agent.
    """
    
    def __init__(self):
        super().__init__(config={})
        self.ka_id = "ka_119_predictive_health"
        self.version = "1.0.0"
        self.description = "Predicts system exhaustion events via trend analysis."
        self.tier = 4

    def _run_logic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute prediction logic.
        """
        if hasattr(params, 'data'):
            params = params.data
            
        metric = params.get("metric_name", "unknown")
        history = params.get("history", [])
        threshold = params.get("threshold", 1000.0)
        
        if len(history) < 3:
            return {"status": "insufficient_data"}
            
        prediction = self._predict_next_value(history)
        
        risk_level = "LOW"
        action = "NONE"
        
        # Risk assessment logic
        if prediction > threshold:
            risk_level = "CRITICAL"
            action = "SCALE_UP" if "usage" in metric else "THROTTLE"
        elif prediction > (threshold * 0.8):
            risk_level = "WARNING"
            action = "PRE_WARM_RESOURCES"
            
        return {
            "status": "success",
            "metric": metric,
            "current_value": history[-1],
            "predicted_next_value": round(prediction, 2),
            "risk_level": risk_level,
            "recommended_action": action
        }

    def _predict_next_value(self, history: List[float]) -> float:
        """
        Simple linear projection based on last 3 points.
        """
        # Calculate recent velocity
        recent_delta = history[-1] - history[-2]
        prev_delta = history[-2] - history[-3]
        
        avg_velocity = (recent_delta + prev_delta) / 2
        
        return history[-1] + avg_velocity
