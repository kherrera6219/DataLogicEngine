from hashlib import sha256
from types import SimpleNamespace

import pytest

from backend.services.local_sentence_embedding import LocalEmbeddingError, LocalSentenceEmbedding


def test_loads_fingerprinted_model_locally_and_reuses_it(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"local weights")
    calls = []

    def loader(path, **kwargs):
        calls.append((path, kwargs))
        return SimpleNamespace(encode=lambda text, **options: [0.6, 0.8])

    embedding = LocalSentenceEmbedding(
        tmp_path,
        expected_weights_sha256=sha256(b"local weights").hexdigest(),
        dimensions=2,
        loader=loader,
    )
    assert embedding("first") == [0.6, 0.8]
    assert embedding("second") == [0.6, 0.8]
    assert len(calls) == 1
    assert calls[0][1] == {"device": "cpu", "local_files_only": True, "trust_remote_code": False}


def test_missing_and_tampered_model_fail_without_loading(tmp_path):
    calls = []
    embedding = LocalSentenceEmbedding(tmp_path, expected_weights_sha256="0" * 64, loader=lambda *args, **kwargs: calls.append(args))
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
        dimensions=2,
        loader=lambda *args, **kwargs: SimpleNamespace(encode=lambda *args, **kwargs: vector),
    )
    with pytest.raises(LocalEmbeddingError, match="vector_invalid"):
        embedding("question")
