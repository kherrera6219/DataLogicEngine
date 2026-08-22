"""Recursive learning helpers for Quad Persona math (no product workflow).

REMOVED (2026-08-21): ``RefinementWorkflow12Step`` (legacy 12-step demo stubs).

Canonical product 12-step refinement is exclusively:
  ``backend.governed_execution.refinement.CanonicalRefinementWorkflow``
registered in the KA manifest under ``authority.refinement_workflow``.

Restore notes: ``docs/archive/audits/LEGACY_REFINEMENT_WORKFLOW_12STEP_REMOVAL_2026-08-21.md``
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Module remains importable for CP19-G legacy non-entrypoint proofs and for
# DeepRecursiveLearning consumers. It is not a product refinement entrypoint.
PRODUCTION_ENTRYPOINT = False
WORKFLOW_DISPOSITION = "removed_legacy_demonstration_reference"


class DeepRecursiveLearning:
    """Implements Deep Recursive Learning with convergence detection."""

    def __init__(
        self,
        max_depth: int = 12,
        epsilon: float = 0.001,
        lambda_param: float = 1.0,
        theta_d: float = 6.0,
    ):
        self.max_depth = max_depth
        self.epsilon = epsilon
        self.lambda_param = lambda_param
        self.theta_d = theta_d
        self.iteration_history = []

    def recursive_processing(
        self, x: np.ndarray, d: int, refinement_fn: callable = None
    ) -> np.ndarray:
        """Recursive Processing Function RPF(x, d)."""
        if d == 0:
            return x

        prev_result = self.recursive_processing(x, d - 1, refinement_fn)

        if refinement_fn:
            return refinement_fn(prev_result)
        return self._default_refinement(prev_result)

    def _default_refinement(self, x: np.ndarray) -> np.ndarray:
        """Default refinement function g(x)."""
        norm = np.linalg.norm(x)
        if norm > 0:
            return x / norm
        return x

    def recursive_confidence_evaluation(self, x: np.ndarray, d: int) -> float:
        """Recursive Confidence Evaluation RCE(x, d)."""
        exponent = self.lambda_param * (d - self.theta_d)
        return 1 - 1 / (1 + math.exp(exponent))

    def convergence_function(self, x_t: np.ndarray, x_t_minus_1: np.ndarray) -> bool:
        """Convergence Function CF(x_t, x_{t-1}, eps)."""
        diff_norm = np.linalg.norm(x_t - x_t_minus_1)
        return diff_norm < self.epsilon

    def deep_recursive_learning(
        self,
        x: np.ndarray,
        context: Dict[str, Any],
        refinement_fns: List[callable] = None,
    ) -> Tuple[np.ndarray, int, float]:
        """Deep Recursive Learning Algorithm DRL(x, c, D)."""
        refinement_fns = refinement_fns or [self._default_refinement] * self.max_depth

        current = x.copy()
        self.iteration_history = [current.copy()]

        for d in range(1, self.max_depth + 1):
            fn_idx = min(d - 1, len(refinement_fns) - 1)
            refined = refinement_fns[fn_idx](current)

            self.iteration_history.append(refined.copy())

            if self.convergence_function(refined, current):
                confidence = self.recursive_confidence_evaluation(refined, d)
                logger.info(
                    f"DRL converged at depth {d} with confidence {confidence:.4f}"
                )
                return refined, d, confidence

            current = refined

        confidence = self.recursive_confidence_evaluation(current, self.max_depth)
        logger.info(
            f"DRL completed max depth {self.max_depth} with confidence {confidence:.4f}"
        )
        return current, self.max_depth, confidence
