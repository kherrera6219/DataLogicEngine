"""Transactional persistence for the canonical governed execution trace."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from extensions import db
from models import (
    ClaimEvidenceLink,
    TraceAxisVector,
    TraceCitation,
    TraceClaim,
    TraceEvidence,
    TraceKAInvocation,
    TracePersona,
    TracePolicyDecision,
    TraceQualityDecision,
    TraceRun,
    TraceStage,
    TraceValidator,
)

logger = logging.getLogger(__name__)


def _stable(run_id: uuid.UUID, kind: str, key: Any) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"datalogicengine:{run_id}:{kind}:{key}")


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _prune(model: Any, run_id: uuid.UUID, primary_key: str, active: set[uuid.UUID]) -> None:
    for record in model.query.filter_by(run_id=run_id).all():
        if getattr(record, primary_key) not in active:
            db.session.delete(record)


def persist_governed_trace(
    gateway: Any,
    sdk_result: dict[str, Any],
    *,
    query: str,
    run_id: str,
    user_id: str,
    session_id: str | None,
    model: str,
) -> bool:
    """Upsert one complete trace and remove rows not present in the executed result."""

    try:
        trace_run_id = gateway._parse_uuid_or_none(run_id)
        if trace_run_id is None:
            logger.warning("Cannot persist non-UUID governed trace ID: %s", run_id)
            return False

        from backend.observability.context import current_correlation_id

        observed_correlation_id = current_correlation_id()
        correlation_id = (
            observed_correlation_id
            if observed_correlation_id not in {"", "startup", "unknown"}
            else None
        )

        metadata = _mapping(sdk_result.get("metadata"))
        dmrf = _mapping(metadata.get("dmrf"))
        axis_vector = _mapping(dmrf.get("axis_vector"))
        gate_result = _mapping(dmrf.get("gate_result"))
        trace = _objects(sdk_result.get("trace"))
        evidence = _objects(sdk_result.get("evidence"))
        claims = _objects(sdk_result.get("claims"))
        citations = _objects(sdk_result.get("citations"))
        validators = _objects(sdk_result.get("validators"))
        usage = _mapping(sdk_result.get("usage"))

        confidence = sdk_result.get("confidence")
        if confidence is None:
            confidence = sdk_result.get("confidence_score")
        total_tokens = usage.get("total_tokens")
        if total_tokens is None:
            total_tokens = _int(usage.get("prompt_tokens")) + _int(usage.get("completion_tokens"))

        run = db.session.get(TraceRun, trace_run_id)
        if run is None:
            run = TraceRun(run_id=trace_run_id)
            db.session.add(run)
        governed_status = str(
            sdk_result.get("status")
            or ("completed" if sdk_result.get("ok", True) else "internal_failure")
        )
        run.session_id = gateway._parse_uuid_or_none(session_id) or run.session_id
        run.user_id = gateway._parse_int_or_none(user_id) or run.user_id
        run.status = governed_status
        run.completed_at = datetime.now(UTC)
        run.model_name = str(sdk_result.get("model_used") or model or "unknown")
        run.model_version = str(
            sdk_result.get("model_version") or metadata.get("model_version") or "unknown"
        )
        run.input_message = query
        run.final_answer = str(sdk_result.get("answer") or "")
        run.correlation_id = correlation_id or run.correlation_id
        run.confidence = _float_or_none(confidence)
        run.tier = str(sdk_result.get("tier") or dmrf.get("tier") or "") or run.tier
        run.layers_executed = [
            str(item.get("stage_name") or item.get("ka_id") or f"stage_{index}")
            for index, item in enumerate(trace)
        ]
        run.truthgate_decision = (
            sdk_result.get("truthgate_decision")
            or gate_result.get("decision")
            or gate_result.get("status")
            or run.truthgate_decision
        )
        run.token_cost = _int(total_tokens)
        run.refinement_cycles = _int(metadata.get("refinement_cycles"))
        if axis_vector.get("frost_layer_depth") is not None:
            run.frost_depth = _int(axis_vector.get("frost_layer_depth"))
        if axis_vector.get("truth_engine_mode"):
            run.truth_engine_mode = str(axis_vector.get("truth_engine_mode"))
        if sdk_result.get("latency_ms") is not None:
            run.latency_ms = _int(sdk_result.get("latency_ms"))
        snapshot = dict(run.data_snapshot or {})
        snapshot.update(
            {
                "contract_version": sdk_result.get("contract_version", "governed.v1"),
                "governed_status": governed_status,
                "provider_used": sdk_result.get("provider_used") or metadata.get("provider_used"),
                "failure": sdk_result.get("failure"),
                "provider_call_count": metadata.get("provider_call_count", 0),
                "source_ids": metadata.get("source_ids", []),
                "confidence_measurement": sdk_result.get("confidence_measurement"),
                "convergence": sdk_result.get("convergence"),
                "convergence_decisions": metadata.get("convergence_decisions", []),
                "dmrf": {
                    "run_id": dmrf.get("run_id"),
                    "query_digest": dmrf.get("query_digest"),
                    "tier": dmrf.get("tier"),
                },
            }
        )
        run.data_snapshot = snapshot
        db.session.flush()

        if axis_vector:
            trace_axis = TraceAxisVector.query.filter_by(run_id=run.run_id).first()
            if trace_axis is None:
                trace_axis = TraceAxisVector(
                    vector_id=_stable(run.run_id, "axis", "vector"),
                    run_id=run.run_id,
                    axes={},
                )
                db.session.add(trace_axis)
            trace_axis.axes = axis_vector.get("axes") or axis_vector
            trace_axis.coordinate_hash = hashlib.sha256(
                json.dumps(trace_axis.axes, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            db.session.flush()
            run.coordinate17_id = trace_axis.vector_id

        active_stages: set[uuid.UUID] = set()
        stage_by_name: dict[str, uuid.UUID] = {}
        for index, item in enumerate(trace):
            name = str(item.get("stage_name") or item.get("ka_id") or f"stage_{index}")
            stage_id = gateway._parse_uuid_or_none(item.get("stage_id")) or _stable(
                run.run_id, "stage", f"{index}:{name}"
            )
            active_stages.add(stage_id)
            stage_by_name[name] = stage_id
            record = db.session.get(TraceStage, stage_id)
            if record is None:
                record = TraceStage(stage_id=stage_id, run_id=run.run_id, name=name)
                db.session.add(record)
            started = gateway._parse_trace_datetime(item.get("start_time"))
            completed = gateway._parse_trace_datetime(item.get("end_time"))
            duration = item.get("duration_ms")
            if duration is None and started and completed:
                duration = max(0, int((completed - started).total_seconds() * 1000))
            record.run_id = run.run_id
            record.name = name
            record.stage_type = str(item.get("stage_type") or "stage")
            record.layer_index = index + 1
            record.step_index = index + 1
            record.status = gateway._normalize_trace_status(item.get("status"))
            record.start_time = started
            record.end_time = completed
            record.duration_ms = _int(duration) if duration is not None else None
            record.inputs = _mapping(item.get("input"))
            record.outputs = _mapping(item.get("output"))
            record.decisions = (
                [{"error_code": item.get("error_code")}] if item.get("error_code") else []
            )
            record.metrics = _mapping(item.get("metrics"))

        retrieval_stage = stage_by_name.get(
            "layer_2_retrieve_context",
            stage_by_name.get("retrieval"),
        )
        validation_stage = stage_by_name.get(
            "layer_6_evidence_validation",
            stage_by_name.get("output_validation"),
        )
        claim_refs: dict[str, list[str]] = {}
        for claim in claims:
            for evidence_id in claim.get("evidence_ids") or []:
                claim_refs.setdefault(str(evidence_id), []).append(str(claim.get("claim_id") or ""))

        active_evidence: set[uuid.UUID] = set()
        evidence_id_map: dict[str, uuid.UUID] = {}
        evidence_hashes: list[str] = []
        for index, item in enumerate(evidence):
            source_id = str(item.get("source_id") or f"source_{index}")
            external_evidence_id = str(item.get("evidence_id") or "")
            evidence_id = gateway._parse_uuid_or_none(external_evidence_id) or _stable(
                run.run_id, "evidence", f"{source_id}:{item.get('content_hash') or index}"
            )
            active_evidence.add(evidence_id)
            evidence_id_map[external_evidence_id or source_id] = evidence_id
            record = db.session.get(TraceEvidence, evidence_id)
            if record is None:
                record = TraceEvidence(evidence_id=evidence_id, run_id=run.run_id)
                db.session.add(record)
            item_metadata = _mapping(item.get("metadata"))
            source = _mapping(item.get("source"))
            record.run_id = run.run_id
            record.source_type = str(item.get("source_type") or "unknown")
            record.source_id = source_id
            record.source_title = item.get("title")
            record.authority = str(item_metadata.get("authority", "medium"))
            record.origin = source.get("origin")
            record.author_publisher = source.get("author_publisher")
            record.captured_at = gateway._parse_trace_datetime(source.get("captured_at"))
            record.effective_at = gateway._parse_trace_datetime(source.get("effective_at"))
            record.retrieved_at = gateway._parse_trace_datetime(item.get("retrieved_at"))
            record.permissions = _mapping(source.get("permissions"))
            record.transformation_chain = _objects(source.get("transformation_chain"))
            record.embedding_revision = source.get("embedding_revision")
            record.locator = _mapping(item.get("locator"))
            record.snippet = str(item.get("text") or "")
            record.content_hash = str(item.get("content_hash") or "")
            record.retrieval_method = str(
                item_metadata.get("retrieval_method") or item.get("source_type") or "unknown"
            )
            record.relevance_score = _float_or_none(item.get("score"))
            record.quality_score = _float_or_none(item.get("quality_score"))
            record.freshness_score = _float_or_none(item.get("freshness_score"))
            record.provenance_completeness = _float_or_none(item.get("provenance_completeness"))
            record.used_by_claims = claim_refs.get(external_evidence_id or source_id, [])
            record.used_by_personas = []
            record.used_by_stages = [str(retrieval_stage)] if retrieval_stage else []
            evidence_hashes.append(record.content_hash or "")
        run.evidence_pack_hash = (
            hashlib.sha256("|".join(sorted(evidence_hashes)).encode("utf-8")).hexdigest()
            if evidence_hashes
            else None
        )

        active_claims: set[uuid.UUID] = set()
        claim_id_map: dict[str, uuid.UUID] = {}
        answer = str(sdk_result.get("answer") or "")
        for index, item in enumerate(claims):
            external_id = str(item.get("claim_id") or f"claim_{index}")
            claim_id = gateway._parse_uuid_or_none(external_id) or _stable(
                run.run_id, "claim", external_id
            )
            active_claims.add(claim_id)
            claim_id_map[external_id] = claim_id
            record = db.session.get(TraceClaim, claim_id)
            if record is None:
                record = TraceClaim(claim_id=claim_id, run_id=run.run_id, text="")
                db.session.add(record)
            text = str(item.get("text") or "")
            explicit_start = item.get("answer_span_start")
            explicit_end = item.get("answer_span_end")
            start = answer.find(text) if text else -1
            record.run_id = run.run_id
            record.text = text
            record.answer_span_start = _int(explicit_start) if explicit_start is not None else (start if start >= 0 else None)
            record.answer_span_end = _int(explicit_end) if explicit_end is not None else (start + len(text) if start >= 0 else None)
            record.status = str(item.get("status") or "unsupported")
            record.confidence = _float_or_none(item.get("confidence"))
            record.claim_type = str(item.get("claim_type") or "factual")
            record.evidence_ids = [
                str(evidence_id_map[str(value)])
                for value in item.get("evidence_ids") or []
                if str(value) in evidence_id_map
            ]
            record.stage_ids = [str(validation_stage)] if validation_stage else []
            record.citation_ids = [str(value) for value in item.get("citation_ids") or []]
        existing_claim_ids = {
            item.claim_id for item in TraceClaim.query.filter_by(run_id=run.run_id).all()
        }
        for record in TraceCitation.query.filter_by(run_id=run.run_id).all():
            db.session.delete(record)
        for record in TraceValidator.query.filter_by(run_id=run.run_id).all():
            db.session.delete(record)
        for link in ClaimEvidenceLink.query.filter(
            ClaimEvidenceLink.claim_id.in_(existing_claim_ids or {uuid.UUID(int=0)})
        ).all():
            db.session.delete(link)
        db.session.flush()
        _prune(TraceClaim, run.run_id, "claim_id", active_claims)
        for item in claims:
            claim_id = claim_id_map.get(str(item.get("claim_id") or ""))
            if claim_id is None:
                continue
            for link in _objects(item.get("evidence_links")):
                evidence_id = evidence_id_map.get(str(link.get("evidence_id") or ""))
                if evidence_id is None:
                    continue
                db.session.add(
                    ClaimEvidenceLink(
                        claim_id=claim_id,
                        evidence_id=evidence_id,
                        confidence=_float_or_none(link.get("score")),
                        relationship=str(link.get("relationship") or "insufficient"),
                        rationale=link.get("rationale"),
                        validator_id=link.get("validator_id"),
                    )
                )

        active_citations: set[str] = set()
        for index, item in enumerate(citations):
            external_id = str(item.get("citation_id") or f"citation_{index}")
            evidence_id = evidence_id_map.get(str(item.get("evidence_id") or ""))
            if evidence_id is None:
                continue
            citation_id = f"{run.run_id}:{external_id}"
            active_citations.add(citation_id)
            record = db.session.get(TraceCitation, citation_id)
            if record is None:
                record = TraceCitation(citation_id=citation_id, run_id=run.run_id)
                db.session.add(record)
            record.run_id = run.run_id
            record.claim_id = claim_id_map.get(str(item.get("claim_id") or ""))
            record.evidence_id = evidence_id
            record.source_id = str(item.get("source_id") or "")
            record.label = str(item.get("label") or "")
            record.answer_span_start = item.get("answer_span_start")
            record.answer_span_end = item.get("answer_span_end")
        _prune(TraceCitation, run.run_id, "citation_id", active_citations)

        active_validators: set[str] = set()
        for index, item in enumerate(validators):
            external_id = str(item.get("validator_id") or f"validator_{index}")
            validator_id = f"{run.run_id}:{external_id}"
            active_validators.add(validator_id)
            record = db.session.get(TraceValidator, validator_id)
            if record is None:
                record = TraceValidator(validator_id=validator_id, run_id=run.run_id)
                db.session.add(record)
            record.run_id = run.run_id
            record.claim_id = claim_id_map.get(str(item.get("claim_id") or ""))
            record.validator_type = str(item.get("validator_type") or "unknown")
            record.version = str(item.get("version") or "unknown")
            record.status = str(item.get("status") or "not_measured")
            record.inputs = _mapping(item.get("inputs"))
            record.outputs = _mapping(item.get("outputs"))
            record.missing_inputs = [str(value) for value in item.get("missing_inputs") or []]
            record.duration_ms = item.get("duration_ms")
        _prune(TraceValidator, run.run_id, "validator_id", active_validators)

        quality_rows: list[tuple[str, dict[str, Any]]] = []
        confidence_measurement = _mapping(sdk_result.get("confidence_measurement"))
        if confidence_measurement:
            quality_rows.append(("confidence", confidence_measurement))
        for item in _objects(metadata.get("convergence_decisions")):
            quality_rows.append(("convergence", item))
        active_quality: set[uuid.UUID] = set()
        for index, (decision_type, item) in enumerate(quality_rows):
            decision_id = _stable(run.run_id, "quality", f"{decision_type}:{index}")
            active_quality.add(decision_id)
            record = db.session.get(TraceQualityDecision, decision_id)
            if record is None:
                record = TraceQualityDecision(decision_id=decision_id, run_id=run.run_id)
                db.session.add(record)
            record.run_id = run.run_id
            record.decision_type = decision_type
            record.version = str(item.get("formula_version") or item.get("decision_version") or "unknown")
            record.status = str(item.get("status") or item.get("action") or "not_measured")
            record.value = _float_or_none(item.get("value"))
            record.components = _mapping(item.get("components")) or item
            record.missing_inputs = item.get("missing_components") or []
            record.rationale = item.get("explanation") or item.get("reason")
            record.iteration = item.get("iteration")
            record.terminal = item.get("terminal")
        _prune(TraceQualityDecision, run.run_id, "decision_id", active_quality)
        _prune(TraceEvidence, run.run_id, "evidence_id", active_evidence)

        dsqp = _mapping(metadata.get("dsqp"))
        profiles = _mapping(dsqp.get("profiles"))
        if not profiles:
            for stage in trace:
                profiles = gateway._dsqp_profiles_from_output(stage.get("output")) or {}
                if profiles:
                    break
        active_personas: set[uuid.UUID] = set()
        for axis_number, item in profiles.items():
            if not isinstance(item, dict):
                continue
            persona_id = _stable(run.run_id, "dsqp", axis_number)
            active_personas.add(persona_id)
            record = db.session.get(TracePersona, persona_id)
            if record is None:
                record = TracePersona(
                    persona_id=persona_id,
                    run_id=run.run_id,
                    persona_type=str(item.get("persona_type") or f"axis_{axis_number}"),
                )
                db.session.add(record)
            validation = _mapping(item.get("validation"))
            profile_metadata = _mapping(item.get("metadata"))
            record.run_id = run.run_id
            record.persona_type = str(item.get("persona_type") or f"axis_{axis_number}")
            record.persona_name = str(item.get("name") or f"Axis {axis_number} Persona")
            record.status = "completed" if validation.get("valid", True) else "failed"
            record.evidence_ids = [str(value.get("source_id")) for value in evidence]
            record.context_scope = str(profile_metadata.get("coordinate_path") or "")
            record.draft_text = str(item.get("description") or "")
            record.confidence = _float_or_none(item.get("coverage_score"))
            record.objections = validation.get("errors") or []
            record.consensus_impact = {
                "construction_mode": profile_metadata.get("construction_mode"),
                "axis_number": item.get("axis_number", axis_number),
                "components": list(_mapping(item.get("components")).keys()),
            }
        _prune(TracePersona, run.run_id, "persona_id", active_personas)

        truthcore = _mapping(metadata.get("truthcore"))
        ka_steps = _objects(truthcore.get("steps_executed"))
        truthcore_stage = stage_by_name.get(
            "layer_1_normalize_route",
            stage_by_name.get("truthcore_preflight"),
        )
        active_kas: set[uuid.UUID] = set()
        for index, item in enumerate(ka_steps):
            ka_id = str(item.get("ka_id") or f"ka_{index}")
            invocation_id = _stable(run.run_id, "ka", f"{index}:{ka_id}")
            active_kas.add(invocation_id)
            record = db.session.get(TraceKAInvocation, invocation_id)
            if record is None:
                record = TraceKAInvocation(
                    invocation_id=invocation_id,
                    run_id=run.run_id,
                    ka_id=ka_id,
                )
                db.session.add(record)
            record.run_id = run.run_id
            record.stage_id = truthcore_stage
            record.ka_id = ka_id
            record.ka_name = str(item.get("step") or ka_id)
            record.ka_version = str(item.get("version") or "runtime")
            record.status = gateway._normalize_trace_status(item.get("status"))
            record.duration_ms = _int(item.get("duration_ms"))
            record.inputs = _mapping(item.get("input"))
            record.outputs = _mapping(item.get("output"))
            record.routing = {"workflow_step": item.get("step"), "mode": truthcore.get("mode")}
            record.side_effects = []
        _prune(TraceKAInvocation, run.run_id, "invocation_id", active_kas)

        decisions = _objects(metadata.get("policy_decisions"))
        active_decisions: set[uuid.UUID] = set()
        for index, item in enumerate(decisions):
            policy_id = str(item.get("policy_id") or f"policy_{index}")
            decision_id = _stable(run.run_id, "policy", f"{index}:{policy_id}")
            active_decisions.add(decision_id)
            record = db.session.get(TracePolicyDecision, decision_id)
            if record is None:
                record = TracePolicyDecision(
                    decision_id=decision_id,
                    run_id=run.run_id,
                    policy_id=policy_id,
                    decision="flag",
                )
                db.session.add(record)
            record.run_id = run.run_id
            record.stage_id = stage_by_name.get(str(item.get("stage") or ""))
            record.policy_id = policy_id
            record.policy_name = str(item.get("policy_name") or policy_id)
            record.rule_id = item.get("rule_id")
            record.decision = str(item.get("decision") or "flag")
            record.rationale = item.get("rationale")
            record.sensitivity_score = _float_or_none(item.get("sensitivity_score"))
            record.modifications = item.get("modifications") if isinstance(item.get("modifications"), list) else []
        _prune(TracePolicyDecision, run.run_id, "decision_id", active_decisions)

        _prune(TraceStage, run.run_id, "stage_id", active_stages)
        db.session.commit()
        logger.info(
            "Persisted governed trace %s: %s stages, %s evidence, %s claims, %s personas, %s KAs, %s policies",
            run.run_id,
            len(active_stages),
            len(active_evidence),
            len(active_claims),
            len(active_personas),
            len(active_kas),
            len(active_decisions),
        )
        return True
    except Exception as exc:
        db.session.rollback()
        logger.warning("Failed to persist governed trace %s: %s", run_id, exc)
        return False
