"""Measured output validation and persisted claim/citation extraction."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from backend.governed_execution.contracts import (
    CitationRecord,
    ClaimRecord,
    EvidenceLinkRecord,
    EvidenceRecord,
    GovernedMode,
    ValidatorRecord,
)
from backend.governed_execution.quality import stable_validator_id


_CITATION_PATTERN = re.compile(r"\[(S\d+)\]")
_SENTENCE_PATTERN = re.compile(r"[^.!?\n]+(?:[.!?]|$)")
_WORD_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.IGNORECASE)
_STOP_WORDS = {
    "the", "and", "that", "this", "with", "from", "into", "for", "are",
    "was", "were", "will", "would", "should", "could", "answer", "source",
}


def validate_output(
    answer: str,
    evidence: list[EvidenceRecord],
    *,
    mode: GovernedMode | str,
    governance_engine: Any,
) -> dict[str, Any]:
    """Validate returned text using observed structure and evidence links."""

    mode = GovernedMode.normalize(mode)
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
    warnings = list(governance_warnings)
    if evidence and not cited:
        warnings.append("retrieved_evidence_not_cited")
    if unknown:
        warnings.append("unknown_citation_labels:" + ",".join(unknown))
    if mode is GovernedMode.ENHANCED and evidence and not cited:
        passed_required = False

    claims, citations, claim_validators = _claims(moderated, known)
    structural_validators = [
        _validator(
            "non_empty",
            "output_structure",
            checks["non_empty"],
            outputs={"non_empty": checks["non_empty"]},
        ),
        _validator(
            "output_policy",
            "policy",
            checks["output_policy_allowed"],
            outputs={"classification": classification},
        ),
        _validator(
            "citation_resolution",
            "citation_resolution",
            checks["citations_known"],
            outputs={"known": cited, "unknown": unknown},
        ),
    ]
    validators = structural_validators + claim_validators
    score = sum(1 for value in checks.values() if value) / len(checks)
    return {
        "ok": passed_required,
        "answer": moderated,
        "classification": classification,
        "checks": checks,
        # Structural check coverage, not answer confidence.
        "validation_score": round(score, 4),
        "cited_labels": cited,
        "unknown_citation_labels": unknown,
        "claims": claims,
        "citations": citations,
        "validators": validators,
        "warnings": warnings,
    }


def _claims(
    answer: str,
    evidence_by_label: dict[str, EvidenceRecord],
) -> tuple[list[ClaimRecord], list[CitationRecord], list[ValidatorRecord]]:
    claims: list[ClaimRecord] = []
    citations: list[CitationRecord] = []
    validators: list[ValidatorRecord] = []
    for sentence_match in _SENTENCE_PATTERN.finditer(answer):
        raw = sentence_match.group(0)
        leading = len(raw) - len(raw.lstrip())
        trailing_text = raw.strip()
        if len(trailing_text) < 8:
            continue
        start = sentence_match.start() + leading
        end = start + len(trailing_text)
        claim_id = "claim_" + sha256(
            f"{start}:{end}:{trailing_text}".encode("utf-8")
        ).hexdigest()[:16]
        links: list[EvidenceLinkRecord] = []
        claim_citation_ids: list[str] = []

        for citation_match in _CITATION_PATTERN.finditer(trailing_text):
            label = citation_match.group(1)
            evidence = evidence_by_label.get(label)
            if evidence is None or evidence.evidence_id is None:
                continue
            relationship, support_score, rationale = _relationship(trailing_text, evidence)
            validator_id = stable_validator_id("claim_support", claim_id)
            links.append(
                EvidenceLinkRecord(
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    relationship=relationship,
                    rationale=rationale,
                    validator_id=validator_id,
                    score=support_score,
                )
            )
            citation_start = start + citation_match.start()
            citation_end = start + citation_match.end()
            citation_id = "citation_" + sha256(
                f"{claim_id}:{evidence.evidence_id}:{citation_start}".encode("utf-8")
            ).hexdigest()[:16]
            citations.append(
                CitationRecord(
                    citation_id=citation_id,
                    label=label,
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    claim_id=claim_id,
                    answer_span_start=citation_start,
                    answer_span_end=citation_end,
                )
            )
            claim_citation_ids.append(citation_id)

        relationships = {link.relationship for link in links}
        if "contradicts" in relationships:
            status = "contradicted"
        elif "supports" in relationships:
            status = "supported"
        else:
            status = "insufficient"
        evidence_ids = [
            link.evidence_id for link in links if link.relationship in {"supports", "contradicts"}
        ]
        claim = ClaimRecord(
            claim_id=claim_id,
            text=trailing_text,
            evidence_ids=evidence_ids,
            status=status,
            confidence=None,
            answer_span_start=start,
            answer_span_end=end,
            claim_type=_claim_type(trailing_text),
            evidence_links=links,
            citation_ids=claim_citation_ids,
        )
        claims.append(claim)
        validator_status = {
            "supported": "passed",
            "contradicted": "failed",
            "insufficient": "not_measured",
        }[status]
        validators.append(
            ValidatorRecord(
                validator_id=stable_validator_id("claim_support", claim_id),
                validator_type="claim_support",
                version="claim-support.v1",
                status=validator_status,
                claim_id=claim_id,
                inputs={
                    "citation_ids": claim_citation_ids,
                    "evidence_ids": [link.evidence_id for link in links],
                },
                outputs={
                    "claim_status": status,
                    "relationships": [link.to_dict() for link in links],
                },
                missing_inputs=["supporting_evidence"] if status == "insufficient" else [],
            )
        )
        if len(claims) >= 50:
            break
    return claims, citations, validators


def _relationship(claim_text: str, evidence: EvidenceRecord) -> tuple[str, float | None, str]:
    explicit = str(evidence.metadata.get("claim_relationship") or "").strip().lower()
    if explicit in {"contradicts", "contradicting", "conflicts"}:
        return "contradicts", None, "Source metadata explicitly marks contradictory evidence."
    if explicit in {"insufficient", "unrelated"}:
        return "insufficient", None, "Source metadata explicitly marks insufficient evidence."

    claim_terms = _terms(_CITATION_PATTERN.sub("", claim_text))
    evidence_terms = _terms(evidence.text)
    if not claim_terms:
        return "insufficient", None, "No factual terms were available for support validation."
    overlap = round(len(claim_terms & evidence_terms) / len(claim_terms), 4)
    if overlap >= 0.2:
        return "supports", overlap, "Citation resolved and met the deterministic term-support threshold."
    return "insufficient", overlap, "Citation resolved but did not meet the term-support threshold."


def _terms(text: str) -> set[str]:
    return {
        token.lower()
        for token in _WORD_PATTERN.findall(text)
        if token.lower() not in _STOP_WORDS
    }


def _claim_type(text: str) -> str:
    lowered = text.lower()
    if lowered.startswith(("i cannot", "i can't", "no provider answer", "local review completed")):
        return "process"
    return "factual"


def _validator(
    key: str,
    validator_type: str,
    passed: bool,
    *,
    outputs: dict[str, Any],
) -> ValidatorRecord:
    return ValidatorRecord(
        validator_id=stable_validator_id(key),
        validator_type=validator_type,
        version="governed-output.v1",
        status="passed" if passed else "failed",
        outputs=outputs,
    )
