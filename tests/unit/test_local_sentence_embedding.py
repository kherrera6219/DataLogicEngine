from hashlib import sha256
from types import SimpleNamespace

import pytest

from backend.services.local_sentence_embedding import (
    LocalEmbeddingError,
    LocalSentenceEmbedding,
    model_manifest_sha256,
)


def _model(encode):
    return SimpleNamespace(encode=encode, max_seq_length=256,
        tokenizer=lambda text, **kwargs:{"input_ids":list(range(len(text.split())+2))})


def test_loads_fingerprinted_model_locally_and_reuses_it(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"local weights")
    calls = []

    def loader(path, **kwargs):
        calls.append((path, kwargs))
        return _model(lambda text, **options: [0.6, 0.8])

    embedding = LocalSentenceEmbedding(
        tmp_path,
        expected_weights_sha256=sha256(b"local weights").hexdigest(),
        expected_manifest_sha256=model_manifest_sha256(tmp_path),
        dimensions=2,
        loader=loader,
    )
    assert embedding("first") == [0.6, 0.8]
    assert embedding("second") == [0.6, 0.8]
    assert len(calls) == 1
    assert calls[0][1] == {
        "device": "cpu",
        "local_files_only": True,
        "trust_remote_code": False,
    }


def test_missing_and_tampered_model_fail_without_loading(tmp_path):
    calls = []
    embedding = LocalSentenceEmbedding(
        tmp_path,
        expected_weights_sha256="0" * 64,
        expected_manifest_sha256="1" * 64,
        loader=lambda *args, **kwargs: calls.append(args),
    )
    with pytest.raises(LocalEmbeddingError, match="model_missing"):
        embedding("question")
    (tmp_path / "model.safetensors").write_bytes(b"unexpected")
    with pytest.raises(LocalEmbeddingError, match="fingerprint_mismatch"):
        embedding("question")
    assert calls == []


@pytest.mark.parametrize("vector", [[0.1], [float("nan"), 0.2], [float("inf"), 0.2]])
def test_bad_embedding_vectors_fail_explicitly(tmp_path, vector):
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    embedding = LocalSentenceEmbedding(
        tmp_path,
        expected_weights_sha256=sha256(b"weights").hexdigest(),
        expected_manifest_sha256=model_manifest_sha256(tmp_path),
        dimensions=2,
        loader=lambda *args, **kwargs: _model(lambda *args, **kwargs: vector),
    )
    with pytest.raises(LocalEmbeddingError, match="vector_invalid"):
        embedding("question")


def test_changed_model_configuration_fails_manifest_check(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    (tmp_path / "config.json").write_text('{"model": "original"}', encoding="utf-8")
    expected_manifest = model_manifest_sha256(tmp_path)
    (tmp_path / "config.json").write_text('{"model": "changed"}', encoding="utf-8")
    embedding = LocalSentenceEmbedding(
        tmp_path,
        expected_weights_sha256=sha256(b"weights").hexdigest(),
        expected_manifest_sha256=expected_manifest,
        loader=lambda *args, **kwargs: pytest.fail("must not load a modified model"),
    )
    with pytest.raises(LocalEmbeddingError, match="manifest_mismatch"):
        embedding("question")


def test_actual_model_capacity_is_used_and_long_input_is_never_silently_truncated(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    encoded=[]
    model = _model(lambda text, **kwargs: encoded.append(text) or [0.6,0.8])
    embedding=LocalSentenceEmbedding(tmp_path, dimensions=2,
        expected_weights_sha256=sha256(b"weights").hexdigest(),
        expected_manifest_sha256=model_manifest_sha256(tmp_path),
        loader=lambda *args, **kwargs:model)
    assert embedding(" ".join(["token"]*254)) == [0.6,0.8]
    with pytest.raises(LocalEmbeddingError, match="input_exceeds_model_limit"):
        embedding(" ".join(["token"]*255))
    assert len(encoded) == 1
