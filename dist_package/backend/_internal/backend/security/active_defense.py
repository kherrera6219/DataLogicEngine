import json
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SecurityVerdict:
    is_safe: bool
    threat_score: float
    threat_type: str
    reason: str
    recommended_action: str

class ActiveDefenseService:
    """
    The Client for the Secondary 'Supervisor' LLM.
    Enforces Active Defense by analyzing intent before execution.
    
    IMPORTANT: This service MUST use a separate API Key from the primary Truth Engine.
    The key is configured in the Admin Settings panel to ensure isolation/non-starvation.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # Key should be loaded from secure Admin Config (Database/Vault), falling back to ENV
        self.api_key = api_key or os.getenv("DEFENSE_LLM_API_KEY", "mock-defense-key")
        self.system_prompt = self._load_prompt()
        
    def _load_prompt(self) -> str:
        try:
            with open("prompts/defense_supervisor.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "You are a Security Supervisor."

    def assess_incoming(self, user_input: str, history_summary: str, user_role: str) -> SecurityVerdict:
        """
        Calls the Secondary LLM to assess the risk of the incoming message.
        Follows a 'Fail-Safe' protocol: If the Supervisor is unreachable, we default to BLOCK
        (or Degradation) to prevent bypassing security during an outage.
        """
        try:
            # In a real implementation, this would call `openai.ChatCompletion` or `anthropic.messages`
            # using `self.api_key` (Isolated Key).
            
            # For this implementation, we simulate the "Reasoning" of the Supervisor
            # based on keyword heuristics that map to the "Constitution".
            
            # Simulate chance of failure if key is invalid (Mock logic)
            if self.api_key == "invalid-key":
                raise ValueError("Authentication Failed with Defense Provider")

            response_json = self._mock_inference(user_input, history_summary)
            
            return SecurityVerdict(
                is_safe=response_json.get("is_safe", False),
                threat_score=response_json.get("threat_score", 1.0),
                threat_type=response_json.get("threat_type", "Unknown"),
                reason=response_json.get("reason", "Analysis Failed"),
                recommended_action=response_json.get("recommended_action", "BLOCK")
            )
            
        except Exception as e:
            self.logger.error(f"Active Defense Supervisor Failed: {str(e)}")
            # FAIL-SAFE: If Supervisor is down, we BLOCK High-Value Actions or 
            # allow only heavily sanitized basic chat. 
            # For "Fortress" mode, we default to BLOCK with specific error.
            return SecurityVerdict(
                is_safe=False,
                threat_score=1.0,
                threat_type="System Failure",
                reason=f"Security Supervisor Unreachable: {str(e)}",
                recommended_action="BLOCK"
            )

    def _mock_inference(self, user_input: str, history: str) -> Dict[str, Any]:
        """
        SIMULATES the Supervisor LLM's logic. 
        In production, this is replaced by the actual API call.
        """
        normalized = user_input.lower()
        
        # 1. Check for Override/Injection
        if "override" in normalized or "ignore" in normalized:
            return {
                "is_safe": False,
                "threat_score": 0.95,
                "threat_type": "Prompt Injection",
                "reason": "User attempted to override system instructions.",
                "recommended_action": "BLOCK"
            }

        # 2. Check for "Crescendo" (Context Poisoning) indicator in history
        # (The caller passes a summary indicating if context is getting weird)
        if "crescendo_risk: high" in history.lower():
             return {
                "is_safe": False,
                "threat_score": 0.85,
                "threat_type": "Crescendo",
                "reason": "Conversation trajectory matches known attack pattern.",
                "recommended_action": "HONEYPOT"
            }
            
        # 3. Check for specific high-risk keywords (DAN mode)
        if "dan mode" in normalized:
             return {
                "is_safe": False,
                "threat_score": 0.99,
                "threat_type": "Social Engineering",
                "reason": "User attempted to invoke DAN persona.",
                "recommended_action": "HONEYPOT"
            }
            
        # Safe
        return {
            "is_safe": True,
            "threat_score": 0.05,
            "threat_type": "None",
            "reason": "Input appears benign.",
            "recommended_action": "ALLOW"
        }
