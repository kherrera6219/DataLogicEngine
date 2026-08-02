"""DPO (Direct Preference Optimization) dataset row builder."""

from __future__ import annotations

import logging
from typing import Any

from .privacy_redactor import PrivacyRedactor
from .schemas import ChatMessage, DPORow
from .sft_builder import SFTBuilder

logger = logging.getLogger(__name__)


class DPOBuilder:
    """Constructs DPOTrainer-compatible preference dataset rows with null safety."""

    @classmethod
    def build_row(
        cls,
        chosen_trace: dict[str, Any],
        rejected_trace: dict[str, Any],
    ) -> DPORow:
        """Construct one DPORow from an evidenced chosen/rejected pair."""
        if not isinstance(chosen_trace, dict):
            chosen_trace = {}
        if not isinstance(rejected_trace, dict):
            rejected_trace = {}

        rejected_answer_raw = rejected_trace.get("rejected_answer") or rejected_trace.get("draft_answer")
        rejected_reason_raw = rejected_trace.get("rejection_reason")
        rejected_source_id = rejected_trace.get("rejected_source_id") or rejected_trace.get("run_id")
        if not rejected_answer_raw or not rejected_reason_raw or not rejected_source_id:
            raise ValueError(
                "DPO export requires a real rejected answer, rejection reason, and rejected source ID."
            )

        query = PrivacyRedactor.redact_text(str(chosen_trace.get("query") or ""))

        prompt_messages = [
            ChatMessage(role="system", content=SFTBuilder.SYSTEM_PROMPT),
            ChatMessage(role="user", content=query),
        ]

        # Chosen completion
        chosen_answer = PrivacyRedactor.redact_text(str(chosen_trace.get("released_answer") or ""))
        chosen_conf = float(chosen_trace.get("confidence", 0.98))
        chosen_content = (
            f"<process_summary>Released by governance (confidence: {chosen_conf:.3f})"
            f"</process_summary>\n<answer>\n{chosen_answer}\n</answer>"
        )
        chosen_messages = [ChatMessage(role="assistant", content=chosen_content)]

        # Rejected completion
        rejected_answer = PrivacyRedactor.redact_text(
            str(rejected_answer_raw)
        )
        rejected_reason = PrivacyRedactor.redact_text(str(rejected_reason_raw))
        if rejected_answer == chosen_answer:
            raise ValueError("DPO chosen and rejected answers must differ.")
        rejected_content = (
            f"<process_summary>Recorded rejection reason: {rejected_reason}</process_summary>"
            f"\n<answer>\n{rejected_answer}\n</answer>"
        )
        rejected_messages = [ChatMessage(role="assistant", content=rejected_content)]

        metadata = {
            "run_id_chosen": str(chosen_trace.get("run_id") or ""),
            "run_id_rejected": str(rejected_source_id),
            "chosen_confidence": chosen_conf,
            "rejected_reason": rejected_reason,
        }

        return DPORow(
            prompt=prompt_messages,
            chosen=chosen_messages,
            rejected=rejected_messages,
            metadata=metadata,
        )
