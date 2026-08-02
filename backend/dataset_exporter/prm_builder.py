"""PRM (Process Reward Model) dataset row builder."""

from __future__ import annotations

import logging
from typing import Any

from .privacy_redactor import PrivacyRedactor
from .schemas import PRMRow

logger = logging.getLogger(__name__)


class PRMBuilder:
    """Constructs status-derived process-label rows with type safety."""

    @classmethod
    def build_row(cls, trace_data: dict[str, Any]) -> PRMRow:
        """Construct one PRMRow safely with step-by-step completions and reward labels."""
        if not isinstance(trace_data, dict):
            trace_data = {}

        query = PrivacyRedactor.redact_text(str(trace_data.get("query") or ""))
        stages = trace_data.get("stages") if isinstance(trace_data.get("stages"), list) else []

        completions: list[str] = []
        labels: list[float] = []

        for idx, stage in enumerate(stages, 1):
            if isinstance(stage, dict):
                stage_name = stage.get("stage", f"Stage {idx}")
                details = PrivacyRedactor.redact_text(str(stage.get("details") or stage.get("status") or "completed"))
                step_text = f"Step {idx} ({stage_name}): {details}"
                completions.append(step_text)

                has_error = stage.get("error") or stage.get("veto") or (stage.get("status") == "failed")
                reward = -1.0 if has_error else 1.0
                labels.append(reward)

        metadata = {
            "run_id": str(trace_data.get("run_id") or ""),
            "total_steps": len(completions),
            "passed_steps": sum(1 for r in labels if r > 0),
            "confidence": float(trace_data.get("confidence", 0.98)),
            "label_source": "recorded_stage_status",
        }

        return PRMRow(
            prompt=query,
            completions=completions,
            labels=labels,
            metadata=metadata,
        )
