import json
import os
import logging
from typing import Optional
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

    async def assess_incoming(self, user_input: str, history_summary: str, user_role: str) -> SecurityVerdict:
        """
        Calls the Secondary LLM to assess the risk of the incoming message.
        Follows a 'Fail-Safe' protocol: If the Supervisor is unreachable, we default to BLOCK
        (or Degradation) to prevent bypassing security during an outage.
        """
        try:
            # Import Gateway here to avoid circular imports during app startup if any
            from backend.llm_gateway.gateway import LLMGateway, GatewayRequest
            
            # Construct the prompt
            start_prompt = self.system_prompt
            final_prompt = f"{start_prompt}\n\nUSER ROLE: {user_role}\nCONTEXT SUMMARY: {history_summary}\n\nINPUT TO ANALYZE: {user_input}"
            
            # Create request for the Gateway with 'security_defense' tier
            gateway = LLMGateway()
            messages = [{"role": "user", "content": final_prompt}]
            
            # This is an internal system call, so we use a system user ID or similar context
            # We must await the gateway call
            response = await gateway.process(GatewayRequest(
                messages=messages,
                mode="json", # Request JSON output if supported by model, or parse text
                meta={"tier": "security_defense", "system_call": True},
                temperature=0.1, # Low temperature for consistent rule enforcement
                max_tokens=500
            ))
            
            if not response.ok:
                raise ValueError(f"Gateway Error: {response.error}")
                
            # Parse the JSON response
            content = response.content
            # Cleanup markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            try:
                response_json = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if model returned plain text despite instructions
                self.logger.warning(f"Defense Supervisor returned non-JSON: {content[:100]}")
                # Conservative fallback
                return SecurityVerdict(
                    is_safe=False,
                    threat_score=0.5,
                    threat_type="Parsing Error",
                    reason="Model output format invalid",
                    recommended_action="BLOCK"
                )

            return SecurityVerdict(
                is_safe=response_json.get("is_safe", False),
                threat_score=float(response_json.get("threat_score", 1.0)),
                threat_type=response_json.get("threat_type", "Unknown"),
                reason=response_json.get("reason", "Analysis Complete"),
                recommended_action=response_json.get("recommended_action", "BLOCK")
            )
            
        except Exception as e:
            self.logger.error(f"Active Defense Supervisor Failed: {str(e)}")
            # FAIL-SAFE: If Supervisor is down, we BLOCK High-Value Actions
            return SecurityVerdict(
                is_safe=False,
                threat_score=1.0,
                threat_type="System Failure",
                reason=f"Security Supervisor Unreachable: {str(e)}",
                recommended_action="BLOCK"
            )

    # _mock_inference removed as it is superseded by live assess_incoming

