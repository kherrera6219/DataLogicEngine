"""DSQP quality gate.

Validates two things for a DSQP persona:

1. **Coverage** — all seven persona components are populated.
2. **Process integrity** — the self-questioning chain was actually executed:
   one step per component, each carrying a non-empty question and answer.

The second check matters for the DSQP claim (`docs/ip/dsqp_technical_disclosure.md`):
the protocol's novelty is the *per-axis seven-step self-questioning process*, so
a persona that happens to have populated components but no recorded chain has not
demonstrably followed the protocol and is not a valid DSQP construction.
"""

from __future__ import annotations

from typing import Any

from backend.dsqp.dsqp_chain import COMPONENT_KEYS


class DSQPValidator:
    """Validate seven-component persona coverage and self-questioning process."""

    def __init__(self, minimum_coverage: float = 0.70):
        self.minimum_coverage = minimum_coverage

    def validate(self, persona: Any) -> dict[str, Any]:
        payload = persona.to_dict() if hasattr(persona, "to_dict") else dict(persona or {})
        components = payload.get("components") or {}
        missing = [
            key
            for key in COMPONENT_KEYS
            if not isinstance(components.get(key), dict)
            or not any(value not in (None, "", [], {}) for value in components[key].values())
        ]
        coverage_score = round((len(COMPONENT_KEYS) - len(missing)) / len(COMPONENT_KEYS), 4)
        coverage_valid = coverage_score >= self.minimum_coverage

        process_valid, process_issues = self._validate_process(payload.get("dsqp_chain"))

        return {
            "valid": coverage_valid and process_valid,
            "coverage_score": coverage_score,
            "missing_components": missing,
            "minimum_coverage": self.minimum_coverage,
            "process_valid": process_valid,
            "process_issues": process_issues,
        }

    @staticmethod
    def _validate_process(chain: Any) -> tuple[bool, list[str]]:
        """Confirm the seven-step self-questioning chain was executed."""
        issues: list[str] = []
        if not isinstance(chain, list):
            return False, ["dsqp_chain_missing"]
        if len(chain) != len(COMPONENT_KEYS):
            issues.append(f"expected_{len(COMPONENT_KEYS)}_steps_got_{len(chain)}")

        seen_components: set[str] = set()
        for index, step in enumerate(chain):
            if not isinstance(step, dict):
                issues.append(f"step_{index}_not_object")
                continue
            component = step.get("component")
            if component in COMPONENT_KEYS:
                seen_components.add(component)
            else:
                issues.append(f"step_{index}_unknown_component:{component}")
            if not str(step.get("question") or "").strip():
                issues.append(f"step_{index}_empty_question")
            if not step.get("answer"):
                issues.append(f"step_{index}_empty_answer")

        missing_steps = [key for key in COMPONENT_KEYS if key not in seen_components]
        if missing_steps:
            issues.append("missing_chain_steps:" + ",".join(missing_steps))

        return (not issues), issues
