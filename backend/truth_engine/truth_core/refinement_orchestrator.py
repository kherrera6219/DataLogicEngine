import asyncio
import logging
from datetime import UTC, datetime
from functools import partial
from typing import Any

from backend.knowledge_algorithms.consumer import execute_required_ka

logger = logging.getLogger(__name__)

PRODUCTION_ENTRYPOINT = False
WORKFLOW_DISPOSITION = "legacy_private_truthcore_compatibility_reference"


class RefinementStep:
    def __init__(self, name: str, ka_id: str, description: str):
        self.name = name
        self.ka_id = ka_id
        self.description = description


class RefinementOrchestrator:
    """
    Orchestrates the 12-step refinement workflow for UKG output.
    Non-production compatibility reference. Canonical production refinement is
    owned by ``backend.governed_execution.refinement``.
    """

    STEPS = [
        RefinementStep("AoT_Polish", "KA-001", "Algorithm of Thought refinement"),
        RefinementStep(
            "Coordinate_Fix", "KA-017", "17-Axis coordinate alignment check"
        ),
        RefinementStep(
            "Nurnburg_Naming", "KA-075", "Standardized naming convention audit"
        ),
        RefinementStep("Contradiction_Sieve", "KA-026", "Final dissonance removal"),
        RefinementStep(
            "Regulatory_Crosswalk", "KA-016", "Multi-jurisdictional law check"
        ),
        RefinementStep(
            "PII_Redaction", "L10-KA-003", "Sanitization and privacy leakage check"
        ),
        RefinementStep("Bias_Neutralization", "KA-010", "Cognitive bias reduction"),
        RefinementStep("Logic_Hardening", "KA-011", "Formal logic validation"),
        RefinementStep("Source_Provenance", "KA-018", "Evidence attribution audit"),
        RefinementStep(
            "Style_Alignment", "KA-057", "Tone and domain-specific language sync"
        ),
        RefinementStep(
            "Safety_Sentinel", "L10-KA-006", "Final Layer 10 release authority"
        ),
        RefinementStep("Memory_Patch", "KA-051", "Recursive memory feedback loop"),
    ]

    def __init__(self, ka_controller: Any):
        self.ka_controller = ka_controller

    async def refine(
        self, initial_response: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Executes the 12-step refinement loop with hardening and confidence gating.
        """
        current_response = initial_response.copy()
        last_good_state = initial_response.copy()
        history = []

        logger.info(
            f"Starting hardened 12-step refinement for initial confidence: {current_response.get('confidence', 0)}"
        )

        for step in self.STEPS:
            try:
                # 1. Execute refinement step
                step_result = await self._execute_step(step, current_response, context)

                # 2. Risk Mitigation: Validate output before committing
                new_confidence = step_result.get("confidence", 0)
                prev_confidence = last_good_state.get("confidence", 0)

                # Security Rule: If confidence drops significantly (>15%), potentially adversarial or error
                if (
                    isinstance(new_confidence, (int, float))
                    and isinstance(prev_confidence, (int, float))
                    and new_confidence < prev_confidence - 0.15
                ):
                    logger.warning(
                        f"Refinement Step {step.name} caused anomaly (conf: {prev_confidence} -> {new_confidence}). Recovering..."
                    )
                    current_response = last_good_state.copy()
                    continue

                # 3. State Update
                current_response.update(step_result)
                last_good_state = current_response.copy()

                history.append(
                    {
                        "step": step.name,
                        "ka_id": step.ka_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "confidence": new_confidence,
                        "confidence_gain": (
                            new_confidence - prev_confidence
                            if isinstance(new_confidence, (int, float))
                            and isinstance(prev_confidence, (int, float))
                            else None
                        ),
                    }
                )

            except Exception as e:
                logger.error(
                    f"Refinement step {step.name} critical failure: {e}. Reverting to last known good state."
                )
                current_response = last_good_state.copy()
                history.append(
                    {
                        "step": step.name,
                        "ka_id": step.ka_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "status": "failed",
                        "error": "Knowledge Algorithm refinement step failed.",
                    }
                )

        current_response["refinement_history"] = history
        current_response["refinement_status"] = (
            "completed"
            if len(history) == len(self.STEPS)
            and all(item.get("status", "executed") != "failed" for item in history)
            else "incomplete"
        )
        try:
            drl_result = self._run_drl_convergence(current_response, context)
            current_response["drl_convergence"] = drl_result
            current_response["confidence_candidates"] = {
                "refinement": current_response.get("confidence"),
                "validator_support": drl_result.get("support_ratio"),
            }
        except Exception as exc:
            logger.debug("Explicit convergence evaluation skipped: %s", exc)
        current_response["final_confidence"] = current_response.get("confidence")

        return current_response

    def _run_drl_convergence(
        self, current_response: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate explicit validator observations; content hashes are not evidence."""

        validators = [
            item
            for item in context.get("validator_results", [])
            if isinstance(item, dict)
        ]
        if not validators:
            return {
                "decision_version": "legacy-explicit-convergence.v1",
                "action": "abstain",
                "terminal": True,
                "support_ratio": None,
                "missing_inputs": ["validator_results"],
                "failed_validator_ids": [],
            }
        failed = [
            str(item.get("validator_id") or "unknown")
            for item in validators
            if item.get("status") == "failed"
        ]
        policy_failed = any(
            item.get("status") == "failed" and item.get("validator_type") == "policy"
            for item in validators
        )
        measured = [
            item for item in validators if item.get("status") in {"passed", "failed"}
        ]
        support_ratio = (
            sum(item.get("status") == "passed" for item in measured) / len(measured)
            if measured
            else None
        )
        return {
            "decision_version": "legacy-explicit-convergence.v1",
            "action": "block"
            if policy_failed
            else ("abstain" if failed else "finalize"),
            "terminal": True,
            "support_ratio": support_ratio,
            "missing_inputs": [] if measured else ["measured_validator_results"],
            "failed_validator_ids": failed,
        }

    async def _execute_step(
        self, step: RefinementStep, content: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Invokes a specific KA for refinement via the Master Controller."""
        try:
            # Prepare KA payload
            ka_input = {
                "query": context.get("query", ""),
                "content": content.get("content", ""),
                "context": context,
                "step_metadata": {
                    "session_id": context.get("session_id"),
                    "step_name": step.name,
                    "convergence_contract": "explicit-validator-inputs",
                },
            }

            # Execute actual KA logic via orchestrator's controller
            # Note: Using run_in_executor if the KA-Master is purely synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                partial(
                    execute_required_ka,
                    self.ka_controller,
                    step.ka_id,
                    ka_input,
                ),
            )
            output = result.require_output()

            refined_content = content.get("content", "")
            content_changed = False
            for field in ("refined_content", "redacted_content", "response"):
                candidate = output.get(field)
                if isinstance(candidate, str) and candidate:
                    refined_content = candidate
                    content_changed = candidate != content.get("content", "")
                    break

            prior_confidence = content.get("confidence")
            measured_confidence = output.get("confidence")
            confidence_changed = isinstance(measured_confidence, (int, float))
            new_confidence = (
                measured_confidence if confidence_changed else prior_confidence
            )

            return {
                "content": refined_content,
                "confidence": new_confidence,
                f"{step.name}_status": "executed",
                "ka_id": result.canonical_id,
                "content_changed": content_changed,
                "confidence_changed": confidence_changed,
                "audit_meta": {
                    "trace_id": result.trace_id,
                    "outcome_type": result.outcome_type.value,
                    "output": output,
                },
            }
        except Exception as e:
            logger.error(f"KA Execution Failed for {step.name} ({step.ka_id}): {e}")
            raise
