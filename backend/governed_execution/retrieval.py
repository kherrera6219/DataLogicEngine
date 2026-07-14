"""Source-identified retrieval for governed execution."""

from __future__ import annotations

import os
from typing import Any

from backend.governed_execution.contracts import EvidenceRecord, GovernedRequest


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
        source_id = str(item.get("id") or "").strip()
        text = str(item.get("text") or "").strip()
        score = float(item.get("score", 0.0) or 0.0)
        if not source_id or not text or source_id in seen or score < min_score:
            continue
        lowered = text.lower()
        if any(marker and marker in lowered for marker in suspicious_markers):
            warnings.append(f"suspicious_retrieval_rejected:{source_id}")
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        citation = item.get("citation") if isinstance(item.get("citation"), dict) else {}
        evidence.append(
            EvidenceRecord(
                source_id=source_id,
                citation_label=f"S{len(evidence) + 1}",
                text=text[:4000],
                source_type=str(citation.get("source_type") or source_kind),
                title=citation.get("source_title") or metadata.get("title") or metadata.get("filename"),
                score=score,
                content_hash=citation.get("content_hash") or metadata.get("content_hash"),
                locator=citation.get("locator") if isinstance(citation.get("locator"), dict) else {},
                metadata={
                    "source_path": citation.get("source_path"),
                    "ingestion_id": citation.get("ingestion_id"),
                    "collection": source_kind,
                },
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
