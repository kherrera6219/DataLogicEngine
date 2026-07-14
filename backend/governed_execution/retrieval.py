"""Source-identified retrieval for governed execution."""

from __future__ import annotations

import os
from hashlib import sha256
import json
from typing import Any
from datetime import UTC, datetime

from backend.governed_execution.contracts import EvidenceRecord, GovernedRequest, SourceRecord


def retrieve_evidence(
    request: GovernedRequest,
    query: str,
    *,
    rag_service: Any | None = None,
) -> tuple[list[EvidenceRecord], list[str]]:
    """Retrieve bounded document, knowledge, and prior-chat evidence.

    The returned IDs and citation labels are the exact identifiers supplied to
    the provider and later accepted by output validation.
    """

    if request.metadata.get("use_rag") is False:
        return [], ["retrieval_disabled_by_request"]

    warnings: list[str] = []
    if rag_service is None:
        try:
            from backend.services.rag_service import get_rag_service

            rag_service = get_rag_service()
        except Exception as exc:
            return [], [f"retrieval_unavailable:{type(exc).__name__}"]

    max_items = _bounded_int(request.constraints.get("max_evidence_items"), 8, 1, 20)
    max_evidence_chars = _bounded_int(
        request.constraints.get("max_evidence_chars"), 12_000, 1_000, 40_000
    )
    max_per_source_kind = _bounded_int(
        request.constraints.get("max_evidence_per_source_kind"),
        max(1, (max_items + 1) // 2),
        1,
        max_items,
    )
    per_source = max(1, min(6, max_items // 2 or 1))
    raw: list[tuple[str, dict[str, Any]]] = []

    try:
        raw.extend(("document", item) for item in rag_service.search_documents(query, k=per_source))
    except Exception as exc:
        warnings.append(f"document_retrieval_failed:{type(exc).__name__}")

    try:
        raw.extend(("knowledge", item) for item in rag_service.search_knowledge(query, k=per_source))
    except Exception as exc:
        warnings.append(f"knowledge_retrieval_failed:{type(exc).__name__}")

    if request.user_id is not None:
        try:
            raw.extend(
                ("chat_memory", item)
                for item in rag_service.search_user_chat_history(
                    user_id=str(request.user_id),
                    query=query,
                    k=per_source,
                    exclude_session_id=request.session_id,
                )
            )
        except Exception as exc:
            warnings.append(f"chat_memory_retrieval_failed:{type(exc).__name__}")

    min_score = _score(request.constraints.get("min_relevance_score"), os.environ.get("RAG_MIN_SCORE", "0.15"))
    suspicious_markers = tuple(
        str(marker).lower()
        for marker in getattr(rag_service, "SUSPICIOUS_RETRIEVAL_MARKERS", ())
    )
    seen: set[str] = set()
    evidence: list[EvidenceRecord] = []
    selected_by_source_kind: dict[str, int] = {}
    selected_characters = 0
    decisions: list[dict[str, Any]] = []
    request.metadata["_retrieval_decisions"] = decisions

    for source_kind, item in sorted(
        raw,
        key=lambda pair: float(pair[1].get("score", 0.0) or 0.0),
        reverse=True,
    ):
        if not isinstance(item, dict):
            decisions.append({"source_kind": source_kind, "disposition": "rejected", "reason": "invalid_result"})
            continue
        text = str(item.get("text") or "").strip()
        score = float(item.get("score", 0.0) or 0.0)
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        citation = item.get("citation") if isinstance(item.get("citation"), dict) else {}
        content_hash = str(
            citation.get("content_hash")
            or metadata.get("content_hash")
            or sha256(text.encode("utf-8")).hexdigest()
        )
        origin = citation.get("source_path") or metadata.get("origin") or metadata.get("source_path")
        source_id = str(item.get("id") or "").strip()
        if not source_id:
            stable_key = f"{source_kind}:{origin or 'unknown'}:{content_hash}"
            source_id = f"source_{sha256(stable_key.encode('utf-8')).hexdigest()[:24]}"
        decision = {
            "source_id": source_id,
            "source_kind": source_kind,
            "score": score,
        }
        if not text:
            decisions.append({**decision, "disposition": "rejected", "reason": "empty_text"})
            continue
        if score < min_score:
            decisions.append({**decision, "disposition": "rejected", "reason": "below_threshold"})
            continue
        if source_id in seen:
            decisions.append({**decision, "disposition": "rejected", "reason": "duplicate"})
            continue
        if selected_by_source_kind.get(source_kind, 0) >= max_per_source_kind:
            decisions.append(
                {**decision, "disposition": "rejected", "reason": "source_diversity_limit"}
            )
            continue
        lowered = text.lower()
        if any(marker and marker in lowered for marker in suspicious_markers):
            warnings.append(f"suspicious_retrieval_rejected:{source_id}")
            decisions.append({**decision, "disposition": "rejected", "reason": "content_defense"})
            continue
        authority_metadata, authority_reason = _validate_ingestion_authority(
            request,
            source_id,
            text,
            metadata,
        )
        if authority_reason:
            warnings.append(f"ingestion_source_rejected:{source_id}:{authority_reason}")
            decisions.append(
                {**decision, "disposition": "rejected", "reason": authority_reason}
            )
            continue
        metadata = {**metadata, **authority_metadata}
        if source_id.startswith("ki_") and request.constraints.get("use_graph_context") is True:
            graph_context, graph_error = _load_graph_context(source_id)
            if graph_error:
                warnings.append(f"graph_context_unavailable:{source_id}:{graph_error}")
                if request.constraints.get("requires_graph_context") is True:
                    decisions.append(
                        {**decision, "disposition": "rejected", "reason": "graph_context_required"}
                    )
                    continue
            if graph_context:
                metadata["graph_context"] = graph_context
        remaining_characters = max_evidence_chars - selected_characters
        if remaining_characters <= 0:
            decisions.append(
                {**decision, "disposition": "rejected", "reason": "evidence_character_budget"}
            )
            continue
        bounded_text = text[: min(4_000, remaining_characters)]
        permissions = _json_object(metadata.get("permissions"))
        transformation_chain = metadata.get("transformation_chain")
        if not isinstance(transformation_chain, list):
            transformation_chain = []
        source_type = str(citation.get("source_type") or metadata.get("source_type") or source_kind)
        title = citation.get("source_title") or metadata.get("title") or metadata.get("filename")
        evidence.append(
            EvidenceRecord(
                source_id=source_id,
                citation_label=f"S{len(evidence) + 1}",
                text=bounded_text,
                source_type=source_type,
                title=title,
                score=score,
                content_hash=content_hash,
                locator=citation.get("locator") if isinstance(citation.get("locator"), dict) else {},
                metadata={
                    "source_path": origin,
                    "ingestion_id": citation.get("ingestion_id"),
                    "collection": source_kind,
                    "source_quality_score": metadata.get("source_quality_score"),
                    "freshness_max_age_days": metadata.get("freshness_max_age_days"),
                    "claim_relationship": metadata.get("claim_relationship"),
                    "source_revision": metadata.get("source_revision"),
                    "document_uid": metadata.get("document_uid"),
                    "retention_class": metadata.get("retention_class"),
                    "retrieval_disposition": "selected",
                    "graph_context": metadata.get("graph_context"),
                },
                source=SourceRecord(
                    source_id=source_id,
                    source_type=source_type,
                    origin=str(origin) if origin is not None else None,
                    title=str(title) if title is not None else None,
                    author_publisher=metadata.get("author_publisher") or metadata.get("author"),
                    captured_at=metadata.get("captured_at") or metadata.get("ingested_at"),
                    effective_at=metadata.get("effective_at") or metadata.get("published_at"),
                    permissions=permissions,
                    transformation_chain=transformation_chain,
                    embedding_revision=metadata.get("embedding_revision"),
                    content_hash=content_hash,
                ),
            )
        )
        decisions.append({**decision, "disposition": "selected", "reason": "eligible"})
        seen.add(source_id)
        selected_by_source_kind[source_kind] = selected_by_source_kind.get(source_kind, 0) + 1
        selected_characters += len(bounded_text)
        if len(evidence) >= max_items:
            break

    return evidence, warnings


def _load_graph_context(source_id: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        from backend.storage import get_graph_store

        graph_store = get_graph_store()
        graph_store.connect()
        return graph_store.get_knowledge_relationships(source_id, limit=12), None
    except Exception as exc:
        return [], type(exc).__name__


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def _validate_ingestion_authority(
    request: GovernedRequest,
    source_id: str,
    text: str,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    """Fail closed for ingestion vectors unless PostgreSQL confirms eligibility."""
    if not source_id.startswith("ki_"):
        return {}, None
    try:
        from flask import has_app_context

        if not has_app_context():
            return {}, "postgresql_authority_unavailable"
        from extensions import db
        from models import IngestionChunk, IngestionFile, IngestionJob

        vector_revision = str(metadata.get("source_revision") or "").strip()
        if not vector_revision:
            return {}, "source_revision_missing"
        candidates = IngestionChunk.query.filter_by(node_uid=source_id).all()
        for chunk in candidates:
            if chunk.source_revision != vector_revision:
                continue
            source_file = db.session.get(IngestionFile, chunk.file_id)
            job = db.session.get(IngestionJob, chunk.job_id)
            if source_file is None or job is None:
                continue
            if job.status != "completed":
                continue
            if source_file.status not in {"ready", "duplicate"}:
                continue
            if (
                source_file.object_status != "ready"
                or source_file.normalized_object_status != "ready"
                or chunk.materialization_state != "ready"
            ):
                continue
            defense = _json_object(source_file.defense_result)
            if (
                defense.get("policy_version") != "content-defense.v1"
                or not defense.get("safe_for_retrieval")
            ):
                return {}, "content_defense_not_approved"
            if sha256(text.encode("utf-8")).hexdigest() != chunk.chunk_sha256:
                return {}, "content_hash_mismatch"
            if job.user_id is not None and request.user_id != job.user_id:
                return {}, "owner_permission_denied"
            request_tenant = request.metadata.get("tenant_id")
            if job.tenant_id and str(request_tenant or "") != str(job.tenant_id):
                return {}, "tenant_permission_denied"
            source_file.last_retrieved_at = datetime.now(UTC)
            source_file.last_retrieval_trace_id = str(
                request.metadata.get("_trace_id") or ""
            ) or None
            db.session.flush()
            return {
                "source_revision": chunk.source_revision,
                "document_uid": source_file.document_uid,
                "retention_class": "ingested_content",
                "content_defense": defense,
                "permissions": {
                    "owner_user_id": job.user_id,
                    "tenant_id": job.tenant_id,
                },
            }, None
        return {}, "postgresql_revision_not_eligible"
    except Exception:
        return {}, "postgresql_authority_unavailable"


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _score(value: Any, fallback: Any) -> float:
    try:
        parsed = float(value if value is not None else fallback)
    except (TypeError, ValueError):
        parsed = 0.15
    return max(0.0, min(1.0, parsed))
