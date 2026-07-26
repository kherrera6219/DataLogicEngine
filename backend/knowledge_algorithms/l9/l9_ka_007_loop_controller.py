"""
L9-KA-007: Loop Controller

Controls recursive iteration:
- Iteration counting
- Diminishing returns detection
- Infinite loop prevention
- Breadcrumb memory
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LoopControllerKA:
    """KA for controlling recursion loops."""

    KA_ID = "L9-KA-007"
    NAME = "Loop Controller"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 5)
        self.min_improvement = self.config.get("min_improvement", 0.03)

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Control recursion loop.

        Args:
            inputs: {"iteration": int, "previous_scores": List[float]}

        Returns:
            {"continue": bool, "reason": str}
        """
        iteration = int(inputs.get("iteration", 0))
        max_iterations = int(inputs.get("max_iterations", self.max_iterations))
        if iteration < 0 or max_iterations < 0:
            raise ValueError("iteration limits must be non-negative")
        prev_scores = inputs.get("previous_scores", [])
        prior_fixes = inputs.get("prior_fixes", [])
        dependency_results = inputs.get("dependency_results") or {}
        refinement_requested = bool(
            (dependency_results.get("L9-KA-005") or {}).get("trigger_refinement")
        )

        if not refinement_requested:
            return {
                "continue": False,
                "reason": "refinement_not_requested",
                "exhausted": False,
            }

        if iteration >= max_iterations:
            logger.info("L9-KA-007: Max iterations (%s) reached", max_iterations)
            return {
                "continue": False,
                "reason": "max_iterations_reached",
                "exhausted": True,
                "terminal_policy": "block_or_abstain_never_force_finalize",
            }

        # Check diminishing returns
        if len(prev_scores) >= 2:
            improvement = prev_scores[-1] - prev_scores[-2]
            if improvement < self.min_improvement:
                logger.info(
                    f"L9-KA-007: Diminishing returns (improvement={improvement:.3f})"
                )
                return {
                    "continue": False,
                    "reason": "diminishing_returns",
                    "improvement": improvement,
                    "exhausted": True,
                }

        # Check for repeated fix attempts
        if (
            len(prior_fixes) > 2
            and len({fix.get("target_layer") for fix in prior_fixes[-3:]}) == 1
        ):
            logger.warning("L9-KA-007: Possible loop detected (same layer targeted 3x)")
            return {
                "continue": False,
                "reason": "possible_loop_detected",
                "exhausted": True,
            }

        logger.info(f"L9-KA-007: Continue allowed (iteration {iteration})")

        return {
            "continue": True,
            "iteration": iteration,
            "remaining": max_iterations - iteration,
            "exhausted": False,
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return LoopControllerKA({}).execute(inputs)
