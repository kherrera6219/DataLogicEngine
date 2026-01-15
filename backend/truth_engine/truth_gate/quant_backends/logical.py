from typing import List, Dict

class LogicalBackend:
    """
    Handles text-based validation (Entropy, Trust, Logic).
    """
    
    def score_claims(self, claims: List[str]) -> Dict[str, float]:
        """
        Scores a list of claims for confidence/entropy.
        Returns map {claim_id: score}
        """
        results = {}
        for i, claim in enumerate(claims):
            cid = f"claim_{i}"
            results[cid] = self._score_text_entropy(claim)
        return results

    def _score_text_entropy(self, text: str) -> float:
        """
        Heuristic entropy scoring.
        Vague words increase entropy (lower confidence).
        """
        vague_indicators = [
            'maybe', 'possibly', 'might', 'could', 'believe', 
            'approximate', 'estimate', 'guess', 'probably'
        ]
        
        normalized = text.lower()
        penalty = 0.0
        
        for word in vague_indicators:
            if word in normalized:
                penalty += 0.2
        
        # Base confidence 1.0, min confidence 0.1
        return max(0.1, 1.0 - penalty)
