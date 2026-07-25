"""KA-1114: bounded external deep-research invocation admission."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA1114Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "sub_question": "What primary evidence supports the claim?",
                    "allowed_domains": ["nist.gov"],
                    "maximum_sources": 10,
                    "timebox_seconds": 300,
                    "connector_id": "research-provider",
                    "connector_approved": True,
                    "policy_approved": True,
                    "human_approved": True,
                }
            ]
        },
    )

    sub_question: str = Field(min_length=5, max_length=10_000)
    allowed_domains: list[str] = Field(min_length=1, max_length=100)
    maximum_sources: int = Field(default=10, ge=1, le=100)
    timebox_seconds: int = Field(default=300, ge=10, le=3_600)
    connector_id: str = Field(min_length=1, max_length=200)
    connector_approved: bool
    policy_approved: bool
    human_approved: bool


class KA1114ExternalDeepResearchInvocation(KnowledgeAlgorithm):
    """Create a stable external-research request; never perform network I/O."""

    input_schema = KA1114Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1114"

    def _run_logic(self, input_data: KA1114Input) -> dict[str, Any]:
        blockers = []
        if not input_data.connector_approved:
            blockers.append("connector_not_approved")
        if not input_data.policy_approved:
            blockers.append("policy_not_approved")
        if not input_data.human_approved:
            blockers.append("human_approval_required")
        request = {
            "sub_question": input_data.sub_question,
            "allowed_domains": sorted(set(input_data.allowed_domains)),
            "maximum_sources": input_data.maximum_sources,
            "timebox_seconds": input_data.timebox_seconds,
            "connector_id": input_data.connector_id,
            "return_contract": "dle.research-evidence-packet.v1",
            "memory_write_allowed": False,
        }
        request_id = hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return {
            "success": True,
            "status": "external_research_invocation_evaluated",
            "decision": "admit" if not blockers else "block",
            "blockers": blockers,
            "request_id": request_id,
            "research_request": request if not blockers else None,
            "provider_called": False,
            "network_accessed": False,
            "memory_written": False,
            "deterministic": True,
            "limitations": (
                "An approved connector must perform bounded research and return "
                "citations for separate validation, trust scoring, and admission."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1114ExternalDeepResearchInvocation(context).run(context)
