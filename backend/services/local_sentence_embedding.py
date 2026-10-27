"""Opt-in local sentence embedding with no implicit model download.

This is a preparation component, not a switch of the active retrieval index.
The embedding revision and all packaged model files must be qualified before
the resulting vectors are used by the application.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from threading import Lock
from typing import Any, Callable


class LocalEmbeddingError(RuntimeError):
    """An explicitly supplied local embedding model cannot be used safely."""


def model_manifest_sha256(path: Path) -> str:
    """Fingerprint every local model file and its relative path, without file contents in logs."""
    root = Path(path)
    if not root.is_dir():
        raise LocalEmbeddingError("local_embedding_model_missing")
    files = sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix())
    if not files or len(files) > 1_000:
        raise LocalEmbeddingError("local_embedding_file_inventory_invalid")
    inventory = hashlib.sha256()
    try:
        for item in files:
            with item.open("rb") as stream:
                file_digest = hashlib.file_digest(stream, "sha256").hexdigest()
            inventory.update(item.relative_to(root).as_posix().encode("utf-8"))
            inventory.update(b"\0")
            inventory.update(file_digest.encode("ascii"))
            inventory.update(b"\n")
    except OSError as exc:
        raise LocalEmbeddingError("local_embedding_files_unreadable") from exc
    return inventory.hexdigest()


class LocalSentenceEmbedding:
    """Lazy-load a caller-supplied, fingerprinted model on the local CPU."""

    def __init__(
        self,
        model_path: Path,
        *,
        expected_weights_sha256: str,
        expected_manifest_sha256: str,
        dimensions: int = 384,
        loader: Callable[..., Any] | None = None,
    ) -> None:
        self.path = Path(model_path)
        self.expected_weights_sha256 = expected_weights_sha256.lower()
        self.expected_manifest_sha256 = expected_manifest_sha256.lower()
        self.dimensions = dimensions
        self._loader = loader
        self._model: Any = None
        self._lock = Lock()

    def _load(self) -> Any:
        with self._lock:
            if self._model is not None:
                return self._model
            weights = self.path / "model.safetensors"
            if not self.path.is_dir() or not weights.is_file():
                raise LocalEmbeddingError("local_embedding_model_missing")
            if len(self.expected_weights_sha256) != 64 or any(
                ch not in "0123456789abcdef" for ch in self.expected_weights_sha256
            ):
                raise LocalEmbeddingError("local_embedding_fingerprint_invalid")
            try:
                with weights.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
            except OSError as exc:
                raise LocalEmbeddingError("local_embedding_weights_unreadable") from exc
            if actual != self.expected_weights_sha256:
                raise LocalEmbeddingError("local_embedding_fingerprint_mismatch")
            if model_manifest_sha256(self.path) != self.expected_manifest_sha256:
                raise LocalEmbeddingError("local_embedding_manifest_mismatch")
            try:
                if self._loader is None:
                    from sentence_transformers import SentenceTransformer

                    self._loader = SentenceTransformer
                model = self._loader(
                    str(self.path.resolve()),
                    device="cpu",
                    local_files_only=True,
                    trust_remote_code=False,
                )
            except Exception as exc:
                raise LocalEmbeddingError("local_embedding_model_unavailable") from exc
            self._model = model
            return model

    def __call__(self, text: str) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise LocalEmbeddingError("local_embedding_text_empty")
        try:
            vector = self._load().encode(
                text, normalize_embeddings=True, show_progress_bar=False
            )
            result = [float(value) for value in vector]
        except LocalEmbeddingError:
            raise
        except Exception as exc:
            raise LocalEmbeddingError("local_embedding_inference_failed") from exc
        if len(result) != self.dimensions or not all(math.isfinite(value) for value in result):
            raise LocalEmbeddingError("local_embedding_vector_invalid")
        return result
