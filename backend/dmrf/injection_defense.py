"""Pure-Python DMRF injection defense."""

from __future__ import annotations

import re


class InjectionDefense:
    """Classify prompt risk into the Phase F categories."""

    NONE = "NONE"
    PROMPT_INJECT = "PROMPT_INJECT"
    LOGICAL_TRAP = "LOGICAL_TRAP"
    OBFUSCATED = "OBFUSCATED"
    PERSONA_HIJACK = "PERSONA_HIJACK"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"

    def detect(self, query: str) -> dict[str, object]:
        text = query or ""
        q = text.lower()
        reasons: list[str] = []
        category = self.NONE

        if re.search(r"(ignore|disregard)\s+(previous|all|system)(?:\s+\w+){0,3}\s+instructions", q):
            category = self.PROMPT_INJECT
            reasons.append("instruction_override")
        elif "this statement is false" in q or "answer 'no' to this" in q:
            category = self.LOGICAL_TRAP
            reasons.append("self_reference")
        elif re.search(r"([A-Za-z0-9+/]{32,}=|[a-f0-9]{64,})", text):
            category = self.OBFUSCATED
            reasons.append("encoded_payload")
        elif "persona" in q and ("ignore" in q or "override" in q or "jailbreak" in q):
            category = self.PERSONA_HIJACK
            reasons.append("persona_override")
        elif len(text) > 50000 or q.count("repeat") > 10 or q.count("summarize") > 5:
            category = self.RESOURCE_EXHAUSTION
            reasons.append("resource_exhaustion")

        return {
            "category": category,
            "safe": category == self.NONE,
            "reasons": reasons,
        }
