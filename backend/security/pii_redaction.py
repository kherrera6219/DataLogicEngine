"""
PII Redaction Middleware
-----------------------
Automatically detects and redacts Personally Identifiable Information (PII)
from user inputs and LLM outputs to prevent data leakage.
"""
import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PIIRedactor:
    """
    Detects and redacts PII using regex patterns and heuristics.
    """
    
    def __init__(self, max_text_length: int = 1000000):
        # Regex patterns for common PII
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        }
        
        self.redaction_map = {}  # Store original -> redacted mapping
        self.max_text_length = max_text_length
        self.redaction_count = 0
        logger.info(f"PIIRedactor initialized (max text length: {max_text_length})")

    
    def redact_text(self, text: str, preserve_format: bool = True) -> Tuple[str, List[str]]:
        """
        Redact PII from text with input validation.
        
        Args:
            text: Input text to redact
            preserve_format: Whether to preserve PII type in redaction
            
        Returns:
            Tuple of (redacted_text, list_of_pii_types_found)
            
        Raises:
            ValueError: If input validation fails
        """
        # Input validation
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        if len(text) > self.max_text_length:
            raise ValueError(f"Text exceeds maximum length of {self.max_text_length} characters")
        
        try:
            redacted = text
            pii_found = []
        
            for pii_type, pattern in self.patterns.items():
                matches = re.findall(pattern, redacted)
                if matches:
                    pii_found.append(pii_type)
                    for match in matches:
                        if preserve_format:
                            # Replace with [REDACTED_TYPE]
                            replacement = f"[REDACTED_{pii_type.upper()}]"
                        else:
                            replacement = "[REDACTED]"
                        redacted = redacted.replace(match, replacement)
                        
                        # Store mapping for audit
                        self.redaction_map[replacement] = match
        
            if pii_found:
                self.redaction_count += len(pii_found)
                logger.warning(f"Redacted PII types: {pii_found} (total redactions: {self.redaction_count})")
            
            return redacted, pii_found
        except Exception as e:
            logger.error(f"PII redaction failed: {e}", exc_info=True)
            # Return original text on error to avoid data loss
            return text, []

    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redact PII from dictionary values.
        """
        redacted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted_data[key], _ = self.redact_text(value)
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self.redact_text(item)[0] if isinstance(item, str) else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        return redacted_data

# Global Instance
pii_redactor = PIIRedactor()


def pii_redaction_middleware(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flask/FastAPI middleware to redact PII from incoming requests.
    """
    return pii_redactor.redact_dict(request_data)
