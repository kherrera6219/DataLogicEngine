"""Exact-source text spans bounded by the selected model's real tokenizer."""

from __future__ import annotations


class ModelChunkingError(RuntimeError):
    """The tokenizer or model budget cannot produce safe source chunks."""


def model_text_chunks(text, tokenizer, model_limit, *, overlap_tokens=32):
    """Reserve required special tokens and use all remaining model capacity."""
    if not isinstance(text, str):
        raise ModelChunkingError("model_chunk_text_invalid")
    if (
        not isinstance(model_limit, int)
        or isinstance(model_limit, bool)
        or not isinstance(overlap_tokens, int)
        or isinstance(overlap_tokens, bool)
    ):
        raise ModelChunkingError("model_chunk_budget_invalid")
    special = tokenizer.num_special_tokens_to_add(pair=False)
    if not isinstance(special, int) or isinstance(special, bool) or special < 0:
        raise ModelChunkingError("model_chunk_special_tokens_invalid")
    budget = model_limit - special
    if budget <= 0 or not 0 <= overlap_tokens < budget:
        raise ModelChunkingError("model_chunk_budget_invalid")
    if not text.strip():
        return []
    offsets = tokenizer(
        text, add_special_tokens=False, truncation=False, return_offsets_mapping=True
    ).get("offset_mapping")
    if not isinstance(offsets, (list, tuple)) or not offsets:
        raise ModelChunkingError("model_chunk_offsets_invalid")
    previous_start = -1
    for span in offsets:
        if (
            not isinstance(span, (list, tuple))
            or len(span) != 2
            or any(
                not isinstance(value, int) or isinstance(value, bool) for value in span
            )
            or not 0 <= span[0] < span[1] <= len(text)
            or span[0] < previous_start
        ):
            raise ModelChunkingError("model_chunk_offsets_invalid")
        previous_start = span[0]
    chunks = []
    start = 0
    while start < len(offsets):
        end = min(start + budget, len(offsets))
        while end > start:
            chunk = text[offsets[start][0] : offsets[end - 1][1]].strip()
            ids = tokenizer(chunk, add_special_tokens=True, truncation=False).get(
                "input_ids"
            )
            if not isinstance(ids, (list, tuple)):
                raise ModelChunkingError("model_chunk_tokens_invalid")
            if chunk and len(ids) <= model_limit:
                break
            end -= 1
        if end == start:
            raise ModelChunkingError("model_chunk_cannot_fit")
        chunks.append(chunk)
        if end == len(offsets):
            break
        start = max(start + 1, end - overlap_tokens)
    return chunks
