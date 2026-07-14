"""Source-identified retrieval for governed execution."""

from __future__ import annotations

import os
from hashlib import sha256
from typing import Any

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

    for source_kind, item in sorted(
        raw,
        key=lambda pair: float(pair[1].get("score", 0.0) or 0.0),
        reverse=True,
    ):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        score = float(item.get("score", 0.0) or 0.0)
        if not text or score < min_score:
            continue
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
        if source_id in seen:
            continue
        lowered = text.lower()
        if any(marker and marker in lowered for marker in suspicious_markers):
            warnings.append(f"suspicious_retrieval_rejected:{source_id}")
            continue
        permissions = metadata.get("permissions")
        if not isinstance(permissions, dict):
            permissions = {}
        transformation_chain = metadata.get("transformation_chain")
        if not isinstance(transformation_chain, list):
            transformation_chain = []
        source_type = str(citation.get("source_type") or metadata.get("source_type") or source_kind)
        title = citation.get("source_title") or metadata.get("title") or metadata.get("filename")
        evidence.append(
            EvidenceRecord(
                source_id=source_id,
                citation_label=f"S{len(evidence) + 1}",
                text=text[:4000],
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
        seen.add(source_id)
        if len(evidence) >= max_items:
            break

    return evidence, warnings


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
