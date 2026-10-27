"""Deterministic local sentence chunking without model downloads or NLP services."""

from __future__ import annotations

import re


CHUNKING_REVISION = "local-sentence-units-v1"
_UNITS = re.compile(r"\w{1,64}|[^\w\s]", re.UNICODE)
_SENTENCE_END = re.compile(r"[.!?。！？][\"'”’)]*$")


def split_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split on sentences within bounded word/punctuation units.

    Units are local text boundaries, not a provider's token count. Long words
    are divided into at most 64-character units so unbroken input is bounded.
    Every chunk preserves an exact span of the original text.
    """
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and 0 <= overlap < chunk_size")
    units = list(_UNITS.finditer(text))
    chunks: list[str] = []
    start = 0
    while start < len(units):
        end = min(start + chunk_size, len(units))
        if end < len(units):
            for boundary in range(end, start + chunk_size // 2, -1):
                left = units[boundary - 1]
                gap = text[left.end() : units[boundary].start()]
                if _SENTENCE_END.search(left.group()) or "\n\n" in gap:
                    end = boundary
                    break
        chunks.append(text[units[start].start() : units[end - 1].end()].strip())
        if end == len(units):
            break
        start = max(start + 1, end - overlap)
    return chunks
