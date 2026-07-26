"""
L9-KA-005: Recursion Trigger

Determines when and why to trigger recursive refinement:
- Threshold violations
- Critical issue detection
- Quality gaps
"""

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class RecursionTriggerKA:
    """KA for determining recursion triggers."""

    KA_ID = "L9-KA-005"
    NAME = "Recursion Trigger"

    # Issue type to target layer mapping
    ROUTING_TABLE: ClassVar[dict[str, int]] = {
        "knowledge_gap": 2,
        "missing_perspective": 4,
        "persona_disagreement": 5,
        "low_quantitative_support": 6,
        "robustness_issues": 7,
        "trust_gate_fail": 8,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.readiness_threshold = self.config.get("readiness_threshold", 0.95)

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Determine if recursion should be triggered.

        Args:
            inputs: {"readiness": float, "issues": List}

        Returns:
            {"trigger_refinement": bool, "target_layer": int, "reason": str}
        """
        dependency_results = inputs.get("dependency_results") or {}
        readiness = inputs.get("readiness")
        if readiness is None:
            readiness_result = dependency_results.get("L9-KA-006") or {}
            if float(readiness_result.get("measurement_coverage") or 0.0) >= 0.6:
                readiness = readiness_result.get("readiness_score")
        issues = inputs.get("issues", [])
        convergence_action = str(inputs.get("convergence_action") or "finalize").lower()
        readiness_threshold = float(
            inputs.get("readiness_threshold", self.readiness_threshold)
        )
        if not 0.0 <= readiness_threshold <= 1.0:
            raise ValueError("readiness_threshold must be between 0 and 1")

        trigger = convergence_action == "refine"
        target_layer = 5  # Default
        reason = ""

        # Check readiness threshold
        if readiness is not None and float(readiness) < readiness_threshold:
            trigger = True
            reason = (
                f"Readiness {float(readiness):.3f} below threshold "
                f"{readiness_threshold}"
            )

        # Check for critical issues
        if issues:
            trigger = True
            # Pick target layer from first issue
            if len(issues) > 0:
                issue_type = (
                    issues[0][0]
                    if isinstance(issues[0], tuple)
                    else issues[0].get("type", "")
                )
                target_layer = self.ROUTING_TABLE.get(issue_type, 5)
                reason = (
                    issues[0][2]
                    if isinstance(issues[0], tuple) and len(issues[0]) > 2
                    else str(issues[0])
                )

        logger.info(f"L9-KA-005: Trigger={trigger}, target_layer={target_layer}")

        return {
            "trigger_refinement": trigger,
            "target_layer": target_layer,
            "reason": reason or f"convergence_action:{convergence_action}",
            "readiness_measured": readiness is not None,
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return RecursionTriggerKA({}).execute(inputs)
