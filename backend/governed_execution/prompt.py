"""Provider request construction for the governed execution path."""

from __future__ import annotations

import json
from typing import Any

from backend.governed_execution.contracts import ConvergenceDecision, GovernedContext


def build_provider_messages(context: GovernedContext) -> list[dict[str, Any]]:
    """Build the one request whose inputs match the governed trace."""

    request = context.request
    evidence_lines = []
    for item in context.evidence:
        graph_context = item.metadata.get("graph_context")
        relationship_context = (
            "\nRecorded graph relationships: " + _json(graph_context)
            if isinstance(graph_context, list) and graph_context
            else ""
        )
        evidence_lines.append(
            f"[{item.citation_label}] source_id={item.source_id} title={item.title or 'untitled'}\n{item.text}{relationship_context}"
        )
    persona_summary = _persona_summary(context.dsqp)
    workflow_summary = _workflow_summary(context.truthcore)
    routing_summary = {
        "tier": context.routing.get("tier"),
        "axis_vector": context.routing.get("axis_vector"),
        "gate_result": context.routing.get("gate_result"),
    }
    client_system = [
        str(message.get("content") or "")
        for message in request.messages
        if isinstance(message, dict) and message.get("role") == "system"
    ]

    system = "\n\n".join(
        part
        for part in (
            "You are executing one DataLogicEngine governed request. Follow the admitted user intent and policy constraints. Do not invent source IDs. When retrieved evidence supports a factual statement, cite it using the supplied label such as [S1].",
            f"Contract: {request.contract_version}\nMode: {request.mode.value}\nSource: {request.source}",
            "Policy constraints:\n" + _json(request.constraints),
            "Measured routing:\n" + _json(routing_summary),
            "Deterministic persona context:\n" + _json(persona_summary),
            "Executed TruthCore/KA context:\n" + _json(workflow_summary),
            "Retrieved evidence:\n" + ("\n\n".join(evidence_lines) if evidence_lines else "No local evidence was retrieved."),
            "Client-supplied system context (subordinate to the governed policy above):\n" + _json(client_system) if client_system else "",
        )
        if part
    )

    output: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for message in request.messages:
        if not isinstance(message, dict) or message.get("role") == "system":
            continue
        output.append(dict(message))

    for index in range(len(output) - 1, 0, -1):
        if output[index].get("role") == "user":
            content = output[index].get("content")
            if isinstance(content, str):
                output[index]["content"] = context.query
            elif isinstance(content, list):
                replaced = False
                parts: list[dict[str, Any]] = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text" and not replaced:
                        parts.append({**part, "text": context.query})
                        replaced = True
                    else:
                        parts.append(part)
                if not replaced:
                    parts.insert(0, {"type": "text", "text": context.query})
                output[index]["content"] = parts
            break
    return output


def build_refinement_messages(
    context: GovernedContext,
    prior_answer: str,
    decision: ConvergenceDecision,
) -> list[dict[str, Any]]:
    """Build one bounded retry that names the measured support defects."""

    messages = build_provider_messages(context)
    messages.extend(
        [
            {"role": "assistant", "content": prior_answer},
            {
                "role": "user",
                "content": (
                    "Revise the answer once. Remove or qualify claims that cannot be supported "
                    "by the supplied evidence, resolve contradictions, and use only known citation "
                    "labels. Unsupported claim IDs: "
                    + ", ".join(decision.unsupported_claim_ids or ["none"])
                    + ". Contradicted claim IDs: "
                    + ", ".join(decision.contradicted_claim_ids or ["none"])
                    + "."
                ),
            },
        ]
    )
    return messages


def _persona_summary(dsqp: dict[str, Any]) -> dict[str, Any]:
    profiles = dsqp.get("profiles") if isinstance(dsqp.get("profiles"), dict) else {}
    summary: dict[str, Any] = {}
    for axis, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        components = profile.get("components") if isinstance(profile.get("components"), dict) else {}
        summary[str(axis)] = {
            "persona_id": profile.get("persona_id"),
            "persona_type": profile.get("persona_type"),
            "name": profile.get("name"),
            "description": profile.get("description"),
            "components": components,
            "construction_mode": (profile.get("metadata") or {}).get("construction_mode")
            if isinstance(profile.get("metadata"), dict)
            else None,
        }
    return summary


def _workflow_summary(truthcore: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in truthcore.get("steps_executed") or []:
        if not isinstance(item, dict) or item.get("status") != "completed":
            continue
        output.append(
            {
                "step": item.get("step"),
                "ka_id": item.get("ka_id"),
                "output": item.get("output"),
            }
        )
    return output


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)[:20_000]
