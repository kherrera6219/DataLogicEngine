"""SFT (Supervised Fine-Tuning) dataset row builder."""

from __future__ import annotations

import logging
from typing import Any

from .privacy_redactor import PrivacyRedactor
from .schemas import ChatMessage, SFTRow

logger = logging.getLogger(__name__)


class SFTBuilder:
    """Constructs SFTTrainer-compatible conversational dataset rows with malformed trace resilience."""

    SYSTEM_PROMPT = (
        "You are a governed AI reasoning engine operating under 17-axis spatial coordinate "
        "constraints, 10-layer reasoning stages, and Quad Persona consensus."
    )

    @classmethod
    def build_row(cls, trace_data: dict[str, Any]) -> SFTRow:
        """Construct one SFTRow safely from a trace_data dictionary."""
        if not isinstance(trace_data, dict):
            logger.warning("Malformed trace_data provided to SFTBuilder: %s", type(trace_data))
            trace_data = {}

        query = PrivacyRedactor.redact_text(str(trace_data.get("query") or ""))
        released_answer = PrivacyRedactor.redact_text(str(trace_data.get("released_answer") or ""))
        stages = trace_data.get("stages") if isinstance(trace_data.get("stages"), list) else []
        personas = trace_data.get("personas") if isinstance(trace_data.get("personas"), list) else []

        summary_lines = ["<process_summary>"]
        for stage in stages:
            if isinstance(stage, dict):
                stage_name = stage.get("stage", stage.get("name", "stage"))
                status = stage.get("status", "completed")
                summary_lines.append(f"Stage {stage_name}: {status}")

        if personas:
            summary_lines.append("Recorded persona summaries:")
            for p in personas:
                if isinstance(p, dict):
                    p_id = p.get("persona_id", p.get("name", "Persona"))
                    p_summary = PrivacyRedactor.redact_text(str(p.get("summary") or ""))
                    summary_lines.append(f"  - {p_id}: {p_summary}")

        summary_lines.append("</process_summary>")
        summary_block = "\n".join(summary_lines)

        assistant_content = f"{summary_block}\n<answer>\n{released_answer}\n</answer>"

        messages = [
            ChatMessage(role="system", content=cls.SYSTEM_PROMPT),
            ChatMessage(role="user", content=query),
            ChatMessage(role="assistant", content=assistant_content),
        ]

        metadata = {
            "run_id": str(trace_data.get("run_id") or ""),
            "tier": trace_data.get("tier", 4),
            "confidence": float(trace_data.get("confidence", 0.98)),
            "axis_vector": trace_data.get("axis_vector") if isinstance(trace_data.get("axis_vector"), dict) else {},
        }

        return SFTRow(messages=messages, metadata=metadata)
