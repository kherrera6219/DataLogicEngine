"""
RAG Sanitizer — Layer 3 Defense: The Sieve.

Sanitizes external content retrieved via RAG to prevent Indirect Prompt Injection.
Pure domain logic; no Flask/DB dependencies.
"""
import re


class RAGSanitizer:
    """
    Sanitizes external content (RAG/docs) to prevent Indirect Prompt Injection.
    """

    # Patterns that look like instructions rather than data
    INJECTION_PATTERNS = [
        r"(?i)ignore (all|previous) instructions",
        r"(?i)system override",
        r"(?i)delete (all|databases)",
        r"(?i)priority override",
        r"(?i)important: forget what you were told",
        r"(?i)new role:",
    ]

    def sanitize_content(self, text: str) -> str:
        """Cleanses text of imperative commands and enforces structural isolation."""
        if not text:
            return ""

        clean_text = text

        for pattern in self.INJECTION_PATTERNS:
            clean_text = re.sub(pattern, "[DATA_SANITIZED: Suspicious Command Removed]", clean_text)

        clean_text = clean_text.replace("### System", "System")
        clean_text = clean_text.replace("### User", "User")

        return clean_text

    def format_for_context(self, text: str, source_id: str) -> str:
        """
        Wraps trusted data in explicit XML tags to enforce 'Data' vs 'Instruction' separation.
        Most modern models respect XML boundaries.
        """
        sanitized = self.sanitize_content(text)
        return f"<document source='{source_id}'>\n{sanitized}\n</document>"
