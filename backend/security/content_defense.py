"""Versioned content-defense policy for untrusted retrieved or ingested text."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from backend.dmrf.injection_defense import InjectionDefense
from backend.security.prompt_injection_shield import PromptInjectionShield


POLICY_VERSION = "content-defense.v1"

_INGESTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        re.compile(r"(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions|prompts)", re.I),
    ),
    (
        "prompt_exfiltration",
        re.compile(r"reveal\s+(?:the\s+)?(?:system|developer)\s+prompt", re.I),
    ),
    ("prompt_boundary", re.compile(r"(?:BEGIN|END)\s+PROMPT", re.I)),
    ("script_markup", re.compile(r"<\s*script\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class ContentDefenseResult:
    """Serializable decision safe to persist beside source authority."""

    policy_version: str
    disposition: str
    safe_for_retrieval: bool
    categories: tuple[str, ...]
    markers_removed: int

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["categories"] = list(self.categories)
        return payload


def evaluate_untrusted_content(text: str) -> tuple[str, ContentDefenseResult]:
    """Normalize text and record a deterministic, versioned defense decision."""
    original = str(text or "").replace("\x00", "")
    categories: set[str] = set()
    markers_removed = 0
    normalized = original

    shield = PromptInjectionShield()
    shield_safe, shield_markers = shield.analyze_prompt(original)
    if not shield_safe:
        categories.update(
            "obfuscated_content" if marker.startswith("obfuscation:") else "prompt_injection"
            for marker in shield_markers
        )
        sanitized = shield.sanitize_prompt(normalized)
        markers_removed += int(sanitized != normalized)
        normalized = sanitized.replace("[REMOVED]", "[removed]")

    dmrf = InjectionDefense().detect(original)
    if not bool(dmrf.get("safe", False)):
        categories.add(str(dmrf.get("category") or "adversarial_content").lower())

    for category, pattern in _INGESTION_PATTERNS:
        normalized, count = pattern.subn("[removed]", normalized)
        if count:
            categories.add(category)
            markers_removed += count

    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{4,}", "\n\n\n", normalized).strip()
    cannot_safely_sanitize = bool(
        categories
        & {
            "obfuscated_content",
            "obfuscated",
            "logical_trap",
            "persona_hijack",
            "resource_exhaustion",
        }
    )
    disposition = (
        "rejected"
        if cannot_safely_sanitize
        else "sanitized"
        if categories
        else "approved"
    )
    return normalized, ContentDefenseResult(
        policy_version=POLICY_VERSION,
        disposition=disposition,
        safe_for_retrieval=bool(normalized) and not cannot_safely_sanitize,
        categories=tuple(sorted(categories)),
        markers_removed=markers_removed,
    )
