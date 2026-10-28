"""Model-aware chunks must fit the actual tokenizer and preserve source text."""

import re

import pytest

from backend.services.model_text_chunking import ModelChunkingError, model_text_chunks


class Tokenizer:
    def num_special_tokens_to_add(self, pair=False):
        assert pair is False
        return 2

    def __call__(self, text, *, add_special_tokens, truncation, return_offsets_mapping=False):
        assert truncation is False
        spans = [match.span() for match in re.finditer(r"\w+|[^\w\s]", text)]
        result = {"input_ids": list(range(len(spans) + (2 if add_special_tokens else 0)))}
        if return_offsets_mapping:
            result["offset_mapping"] = spans
        return result


def test_chunks_use_full_model_capacity_and_cover_exact_unicode_source_spans():
    text = "Пример " + " ".join(f"unique{i}" for i in range(40)) + " 日本語."
    tokenizer = Tokenizer()
    chunks = model_text_chunks(text, tokenizer, 10, overlap_tokens=2)
    assert len(chunks) > 1
    assert all(chunk in text for chunk in chunks)
    lengths = [len(tokenizer(chunk, add_special_tokens=True, truncation=False)["input_ids"]) for chunk in chunks]
    assert max(lengths) == 10
    assert all(length <= 10 for length in lengths)
    for token in re.findall(r"\w+|[^\w\s]", text):
        assert any(token in chunk for chunk in chunks)
    assert chunks[0].startswith("Пример")
    assert chunks[-1].endswith("日本語.")


def test_short_input_is_preserved_and_empty_input_has_no_chunks():
    assert model_text_chunks("short source", Tokenizer(), 256) == ["short source"]
    assert model_text_chunks("   ", Tokenizer(), 256) == []


@pytest.mark.parametrize("limit,overlap", [(0,0), (2,0), (10,8), (10,-1)])
def test_invalid_model_budget_fails_explicitly(limit, overlap):
    with pytest.raises(ModelChunkingError):
        model_text_chunks("source", Tokenizer(), limit, overlap_tokens=overlap)


def test_unusable_tokenizer_offsets_fail_explicitly():
    class BrokenTokenizer(Tokenizer):
        def __call__(self, *args, **kwargs):
            return {"offset_mapping": [(999,1000)]}
    with pytest.raises(ModelChunkingError):
        model_text_chunks("source", BrokenTokenizer(), 256)
