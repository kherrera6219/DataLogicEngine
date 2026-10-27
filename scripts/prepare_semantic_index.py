"""Prepare an existing local shadow collection; never activate or delete it.

Example: python -m scripts.prepare_semantic_index --help
The operator must provision a distinct target with matching revision metadata
and quiesce the source first. This is not an installed migration or cutover.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.services.local_sentence_embedding import LocalSentenceEmbedding
from backend.storage.chroma_http import ChromaHttpClient
from backend.storage.chroma_security import safe_get_collection
from backend.storage.semantic_index_preparation import prepare_semantic_index


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", type=int, required=True, help="Local Chroma service port"
    )
    parser.add_argument("--source", required=True, help="Existing source collection")
    parser.add_argument(
        "--target", required=True, help="Existing separate target collection"
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        required=True,
        help="Existing qualified local model folder",
    )
    parser.add_argument("--weights-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--revision",
        required=True,
        help="Target revision containing the model inventory SHA-256",
    )
    parser.add_argument("--max-records", type=int, default=10_000)
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args(argv)
    fingerprint = args.manifest_sha256.lower()
    if len(fingerprint) != 64 or fingerprint not in args.revision.lower():
        parser.error("revision must contain the full model inventory SHA-256")
    if args.source == args.target:
        parser.error("source and target must be different collections")
    embedding = LocalSentenceEmbedding(
        args.model_path,
        expected_weights_sha256=args.weights_sha256,
        expected_manifest_sha256=fingerprint,
    )
    # Qualify the model before contacting or writing the target.
    embedding("Local embedding preparation preflight.")
    with ChromaHttpClient(host="127.0.0.1", port=args.port) as client:
        source = safe_get_collection(client, name=args.source)
        target = safe_get_collection(client, name=args.target)
        receipt = prepare_semantic_index(
            source,
            target,
            embedding,
            embedding_revision=args.revision,
            batch_size=args.batch_size,
            max_records=args.max_records,
        )
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
