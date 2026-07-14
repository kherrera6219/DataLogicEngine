"""Measured output validation and claim/citation extraction."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from backend.governed_execution.contracts import ClaimRecord, EvidenceRecord, GovernedMode


_CITATION_PATTERN = re.compile(r"\[(S\d+)\]")
_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


def validate_output(
    answer: str,
    evidence: list[EvidenceRecord],
    *,
    mode: GovernedMode,
    governance_engine: Any,
) -> dict[str, Any]:
    """Validate the returned text using only observed checks."""

    moderated, classification, governance_warnings = governance_engine.apply_output_controls(answer)
    known = {item.citation_label: item for item in evidence}
    cited_labels = _CITATION_PATTERN.findall(moderated)
    unknown = sorted(set(cited_labels) - set(known))
    cited = sorted(set(cited_labels) & set(known))
    checks = {
        "non_empty": bool(moderated.strip()),
        "output_policy_allowed": moderated != "Response withheld by safety policy.",
        "citations_known": not unknown,
        "evidence_cited": not evidence or bool(cited),
    }
    required = ["non_empty", "output_policy_allowed", "citations_known"]
    passed_required = all(checks[name] for name in required)
    score = sum(1 for value in checks.values() if value) / len(checks)
    warnings = list(governance_warnings)
    if evidence and not cited:
        warnings.append("retrieved_evidence_not_cited")
    if unknown:
        warnings.append("unknown_citation_labels:" + ",".join(unknown))
    if mode is GovernedMode.ENHANCED and evidence and not cited:
        passed_required = False

    claims = _claims(moderated, known)
    return {
        "ok": passed_required,
        "answer": moderated,
        "classification": classification,
        "checks": checks,
        "validation_score": round(score, 4),
        "cited_labels": cited,
        "unknown_citation_labels": unknown,
        "claims": claims,
        "warnings": warnings,
    }


def _claims(answer: str, evidence_by_label: dict[str, EvidenceRecord]) -> list[ClaimRecord]:
    claims: list[ClaimRecord] = []
    for sentence in _SENTENCE_PATTERN.split(answer):
        text = sentence.strip()
        if len(text) < 8:
            continue
        labels = _CITATION_PATTERN.findall(text)
        evidence_ids = [
            evidence_by_label[label].source_id
            for label in labels
            if label in evidence_by_label
        ]
        claim_id = "claim_" + sha256(text.encode("utf-8")).hexdigest()[:16]
        claims.append(
            ClaimRecord(
                claim_id=claim_id,
                text=text,
                evidence_ids=evidence_ids,
                status="supported" if evidence_ids else "unsupported",
                # Phase 6 owns the versioned confidence formula. Citation
                # presence establishes support state, not numeric confidence.
                confidence=None,
            )
        )
        if len(claims) >= 50:
            break
    return claims
