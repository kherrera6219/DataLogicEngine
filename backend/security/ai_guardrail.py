import re
import base64
from typing import Optional, Tuple

class AIGuardrailService:
    """
    Layer 1 Defense: The Gatekeeper.
    sits outside the model reasoning space to block structural attacks and prohibited inputs.
    """
    
    PROHIBITED_PHRASES = [
        "ignore previous instructions",
        "ignore all instructions",
        "bypass security",
        "system override",
        "developer mode",
        "god mode",
        "dan mode",
        "do anything now"
    ]
    
    # Simple heuristics for structural anomalies
    LEETSPEAK_MAP = str.maketrans("430157", "aeolst")

    def validate_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Scans user input for malicious intent before it reaches the LLM.
        Returns: (is_safe, rejection_reason)
        """
        normalized_input = user_input.lower()
        
        # 1. Check Prohibited Phrases
        for phrase in self.PROHIBITED_PHRASES:
            if phrase in normalized_input:
                return False, f"Prohibited prohibited phrase detected: '{phrase}'"
            
        # 2. Check for Base64 Encoding usage (heuristic)
        # Matches typical base64 strings if they are long enough (e.g. > 20 chars) and look valid
        if self._detect_base64_payload(user_input):
            return False, "Obfuscated payload detected (Base64)"
            
        # 3. Check for Leetspeak variants of prohibited phrases
        # Decode numbers to letters and check prohibited phrases again
        decoded_leet = normalized_input.translate(self.LEETSPEAK_MAP)
        for phrase in self.PROHIBITED_PHRASES:
            if phrase in decoded_leet:
                return False, f"Obfuscated prohibited phrase detected (Leetspeak): '{phrase}'"
                
        return True, None

    # PII patterns used by validate_output to block sensitive data leakage.
    # Ordered from most specific (SSN) to most general (email) to reduce false positives.
    _PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",                        # SSN (US)
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b",                  # Credit card (16-digit)
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",            # Phone number (US)
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
    ]

    def validate_output(self, llm_output: str) -> Tuple[bool, Optional[str]]:
        """
        Scans LLM output for leakage.
        Returns: (is_safe, redaction_notice)
        """
        # 1. Check for System Prompt Leakage
        # If the model starts repeating its own instructions
        if "you are a helpful ai assistant" in llm_output.lower() and len(llm_output) < 200:
            return False, "[BLOCKED: Potential System Output Leakage]"

        # 2. Check for PII Leakage — SSN, credit card, phone, and email patterns.
        for pattern in self._PII_PATTERNS:
            if re.search(pattern, llm_output):
                return False, "[BLOCKED: PII Detected in Output]"

        return True, None

    def _detect_base64_payload(self, text: str) -> bool:
        """
        Detects Base64-encoded payloads that embed prohibited phrases.
        Only flags tokens whose decoded content actually matches the prohibited phrase list —
        this avoids blocking legitimate base64-encoded images or file attachments.
        """
        tokens = text.split()
        for token in tokens:
            if len(token) > 20 and re.match(r'^[A-Za-z0-9+/]+={0,2}$', token):
                try:
                    decoded_bytes = base64.b64decode(token, validate=True)
                    decoded_text = decoded_bytes.decode('utf-8', errors='ignore').lower()
                    for phrase in self.PROHIBITED_PHRASES:
                        if phrase in decoded_text:
                            return True
                except Exception:
                    continue
        return False
