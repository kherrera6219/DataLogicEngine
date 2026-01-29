"""
Prompt Injection Shield
----------------------
Detects and blocks prompt injection attacks using pattern matching
and heuristic analysis.
"""
import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PromptInjectionShield:
    """
    Detects malicious prompt injection attempts.
    """
    
    def __init__(self):
        # Suspicious patterns that indicate injection attempts
        self.injection_patterns = [
            r'ignore\s+(all\s+)?previous\s+instructions',
            r'disregard\s+(all\s+)?prior\s+(instructions|prompts)',
            r'you\s+are\s+now\s+a',
            r'forget\s+(everything|all)',
            r'new\s+instructions:',
            r'system\s+override',
            r'admin\s+mode',
            r'developer\s+mode',
            r'jailbreak',
            r'jailbroken',
            r'DAN\s+mode',  # "Do Anything Now"
            r'pretend\s+you\s+are',
            r'act\s+as\s+if',
        ]
        
        # Obfuscation detection
        self.obfuscation_patterns = [
            r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64
            r'\\x[0-9a-fA-F]{2}',  # Hex encoding
            r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Potential crypto addresses
        ]
        
        self.blocked_count = 0
        logger.info("PromptInjectionShield initialized")
    
    def analyze_prompt(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Analyze a prompt for injection attempts.
        
        Returns:
            Tuple of (is_safe, list_of_detected_patterns)
        """
        detected_patterns = []
        prompt_lower = prompt.lower()
        
        # Check for direct injection patterns
        for pattern in self.injection_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                detected_patterns.append(f"injection:{pattern}")
        
        # Check for obfuscation
        for pattern in self.obfuscation_patterns:
            if re.search(pattern, prompt):
                detected_patterns.append(f"obfuscation:{pattern}")
        
        # Heuristic: Excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', prompt)) / max(len(prompt), 1)
        if special_char_ratio > 0.3:
            detected_patterns.append("high_special_char_ratio")
        
        # Heuristic: Repetitive patterns
        if re.search(r'(.{10,})\1{3,}', prompt):
            detected_patterns.append("repetitive_pattern")
        
        is_safe = len(detected_patterns) == 0
        
        if not is_safe:
            self.blocked_count += 1
            logger.warning(f"Prompt injection detected: {detected_patterns}")
        
        return is_safe, detected_patterns
    
    def sanitize_prompt(self, prompt: str) -> str:
        """
        Attempt to sanitize a potentially malicious prompt.
        """
        # Remove common injection keywords
        sanitized = prompt
        for pattern in self.injection_patterns:
            sanitized = re.sub(pattern, '[REMOVED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized

# Global Instance
prompt_shield = PromptInjectionShield()


def validate_user_input(user_input: str, strict_mode: bool = True) -> Dict[str, Any]:
    """
    Validate user input for prompt injection.
    
    Returns:
        {
            "is_safe": bool,
            "detected_patterns": List[str],
            "sanitized_input": str
        }
    """
    is_safe, patterns = prompt_shield.analyze_prompt(user_input)
    
    if not is_safe and strict_mode:
        raise ValueError(f"Prompt injection detected: {patterns}")
    
    return {
        "is_safe": is_safe,
        "detected_patterns": patterns,
        "sanitized_input": prompt_shield.sanitize_prompt(user_input) if not is_safe else user_input
    }
