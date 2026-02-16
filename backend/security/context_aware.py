from typing import List, Dict, Any
import logging

class ContextDriftDetector:
    """
    Layer 2 Defense: The Watchtower.
    protects against 'Crescendo' (multi-turn) attacks by distinguishing proper context
    from gradual context poisoning.
    """
    
    def __init__(self, history_window: int = 5):
        self.history_window = history_window
        # Simulated risk scores for topics: 0.0 (Safe) to 1.0 (Danger)
        # In a real system, this would use a Zero-Shot classification model.
        self.SENSITIVE_TOPICS = {
            "explosives": 0.9,
            "chemistry": 0.2, # Benign starter topic
            "hacking": 0.8,
            "coding": 0.1,    # Benign starter topic
            "bypass": 0.9,
            "system": 0.1
        }
        self.logger = logging.getLogger(__name__)

    def analyze_trajectory(self, session_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyzes the last N turns for risk velocity.
        
        Args:
            session_history: List of {"role": "user", "content": "..."}
        
        Returns:
            {
                "is_safe": bool,
                "risk_velocity": float,
                "reason": str
            }
        """
        if not session_history:
            return {"is_safe": True, "risk_velocity": 0.0, "reason": "No history"}

        # Look at last N user messages
        recent_turns = [
            turn["content"] for turn in session_history 
            if turn["role"] == "user"
        ][-self.history_window:]
        
        risk_scores = [self._score_content(text) for text in recent_turns]
        
        if not risk_scores:
            return {"is_safe": True, "risk_velocity": 0.0, "reason": "No user content"}
            
        # Calculate Risk Velocity (Trend)
        # If scores are increasing [0.1, 0.3, 0.5, 0.8], velocity is positive/high
        
        if len(risk_scores) < 2:
            current_risk = risk_scores[0]
            if current_risk > 0.8:
                 return {"is_safe": False, "risk_velocity": 1.0, "reason": "Immediate High Risk Input"}
            return {"is_safe": True, "risk_velocity": 0.0, "reason": "Insufficient history"}

        velocity = self._calculate_velocity(risk_scores)
        current_risk = risk_scores[-1]
        
        # Heuristic: If velocity is consistently positive AND we end up at a high risk context
        if velocity > 0.15 and current_risk > 0.6:
            return {
                "is_safe": False, 
                "risk_velocity": velocity, 
                "reason": f"Crescendo Attack Detected (Velocity: {velocity:.2f})"
            }

        # Absolute limit
        if current_risk > 0.85:
            return {"is_safe": False, "risk_velocity": 0.0, "reason": "Context saturated with prohibited topic"}

        return {"is_safe": True, "risk_velocity": velocity, "reason": "Normal flow"}

    def _score_content(self, text: str) -> float:
        """
        Simulated Zero-Shot classification score.
        """
        text = text.lower()
        max_score = 0.0
        for topic, score in self.SENSITIVE_TOPICS.items():
            if topic in text:
                max_score = max(max_score, score)
        return max_score

    def _calculate_velocity(self, scores: List[float]) -> float:
        """
        Simple linear regression slope or delta average to forward velocity.
        """
        if len(scores) < 2: return 0.0
        
        deltas = []
        for i in range(1, len(scores)):
            deltas.append(scores[i] - scores[i-1])
            
        # Average invalid step-up
        return sum(deltas) / len(deltas)
