"""Model-aware chunks must fit the actual tokenizer and preserve source text."""

import re

import pytest

from backend.services.model_text_chunking import ModelChunkingError, model_text_chunks


class Tokenizer:
    def num_special_tokens_to_add(self, pair=False):
        assert pair is False
        return 2

    def __call__(self, text, *, add_special_tokens, truncation, return_offsets_mapping=False, verbose=True):
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


def test_configured_local_model_ingests_every_document_span_without_truncation(tmp_path):
    from hashlib import sha256
    from types import SimpleNamespace
    from backend.services.local_sentence_embedding import LocalSentenceEmbedding, model_manifest_sha256
    from backend.services.rag_service import RAGService

    (tmp_path / "model.safetensors").write_bytes(b"synthetic weights")
    tokenizer = Tokenizer()
    encoded = []
    def encode(text, **kwargs):
        assert len(tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]) <= 10
        encoded.append(text)
        return [0.6, 0.8]
    embed = LocalSentenceEmbedding(tmp_path, dimensions=2,
        expected_weights_sha256=sha256(b"synthetic weights").hexdigest(),
        expected_manifest_sha256=model_manifest_sha256(tmp_path),
        loader=lambda *a, **k: SimpleNamespace(max_seq_length=10, tokenizer=tokenizer, encode=encode))
    written = []
    def store(**kwargs):
        written.append(kwargs)
        return kwargs["ids"]
    def replace(collection, parent_id, **kwargs):
        assert collection == "documents"
        assert parent_id == "synthetic-doc"
        return store(collection=collection, **kwargs)
    service = RAGService(vector_store=SimpleNamespace(replace_embeddings=replace), embedding_provider=embed)
    text = " ".join(f"unique{i}" for i in range(40))
    count = service.ingest_document("synthetic-doc", text, {"user_id":"owner"})
    assert count > 1
    assert count == len(encoded) == len(written[0]["ids"])
    assert written[0]["texts"] == encoded
    assert all(value in text for value in encoded)
    assert all(any(token in part for part in encoded) for token in text.split())
    assert all(meta["user_id"] == "owner" for meta in written[0]["metadata"])
