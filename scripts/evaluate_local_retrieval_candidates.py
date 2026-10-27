"""Compare offline retrieval candidates on a small synthetic screening set.

This does not access customer data or modify indexes. The caller supplies an
existing local model directory; no model download or provider call is allowed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from math import sqrt
from pathlib import Path
import re
from time import perf_counter

from backend.services.rag_service import RAGService


DOCUMENTS = [
    "Refunds are available within thirty days of purchase with a receipt.",
    "Employees must report suspected phishing messages to the security team.",
    "Encrypted backups are created each night and retained for ninety days.",
    "The capital of France in the fourteenth century was Paris.",
    "The company permits remote work two days per week with manager approval.",
    "The database connection uses a local PostgreSQL service on the workstation.",
    "Annual vacation requests must be approved by a supervisor before booking.",
    "An emergency outage should be escalated to the on-call operations engineer.",
]
QUERIES = [
    ("How long after buying can a customer get money back?", 0),
    ("Where should a worker report a suspicious email?", 1),
    ("How long are nightly backups kept?", 2),
    ("Which city was the French capital in 1342?", 3),
    ("How often may staff work from home?", 4),
    ("Which relational database runs locally?", 5),
    ("Who must authorize a holiday request?", 6),
    ("Who handles an urgent system failure?", 7),
]


def cosine(left: list[float], right: list[float]) -> float:
    denominator = sqrt(sum(x * x for x in left) * sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right)) / denominator if denominator else 0.0


def lexical_similarity(left: str, right: str) -> float:
    a = Counter(re.findall(r"[a-z0-9]+", left.lower()))
    b = Counter(re.findall(r"[a-z0-9]+", right.lower()))
    denominator = sqrt(sum(x * x for x in a.values()) * sum(x * x for x in b.values()))
    return sum(value * b[token] for token, value in a.items()) / denominator if denominator else 0.0


def metrics(rankings: list[list[int]]) -> tuple[int, int]:
    return (
        sum(ranking[0] == target for ranking, (_, target) in zip(rankings, QUERIES)),
        sum(target in ranking[:4] for ranking, (_, target) in zip(rankings, QUERIES)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path, help="Existing local model directory")
    args = parser.parse_args()
    model_path = args.model_path.resolve(strict=True)
    if not model_path.is_dir():
        raise ValueError("model_path must be an existing local directory")

    from sentence_transformers import SentenceTransformer

    started = perf_counter()
    model = SentenceTransformer(str(model_path), device="cpu", local_files_only=True, trust_remote_code=False)
    model_load_seconds = perf_counter() - started
    started = perf_counter()
    embeddings = model.encode(DOCUMENTS + [query for query, _ in QUERIES], normalize_embeddings=True, show_progress_bar=False)
    model_encode_seconds = perf_counter() - started
    semantic_docs = [list(map(float, row)) for row in embeddings[: len(DOCUMENTS)]]
    semantic_queries = [list(map(float, row)) for row in embeddings[len(DOCUMENTS) :]]
    baseline = RAGService()
    baseline_docs = [baseline._deterministic_embedding(doc) for doc in DOCUMENTS]
    ranking_sets: dict[str, list[list[int]]] = {"hash_projection": [], "lexical": [], "local_semantic": []}
    for index, (query, _) in enumerate(QUERIES):
        query_vector = baseline._deterministic_embedding(query)
        scores = {
            "hash_projection": [cosine(query_vector, doc) for doc in baseline_docs],
            "lexical": [lexical_similarity(query, doc) for doc in DOCUMENTS],
            "local_semantic": [cosine(semantic_queries[index], doc) for doc in semantic_docs],
        }
        for name, values in scores.items():
            ranking_sets[name].append(sorted(range(len(values)), key=lambda item: (-values[item], item)))
    print(f"Synthetic screening set: {len(DOCUMENTS)} documents, {len(QUERIES)} queries")
    print("Metric: cosine or token-frequency cosine; ranking only; no Chroma or threshold test")
    for name, rankings in ranking_sets.items():
        top1, top4 = metrics(rankings)
        print(f"{name}: top1={top1}/{len(QUERIES)}, recall_at_4={top4}/{len(QUERIES)}")
    print(f"Local semantic model load={model_load_seconds:.2f}s; encode 16 texts={model_encode_seconds:.2f}s")
    print("Synthetic screening only; not production accuracy, security, latency, or migration evidence.")


if __name__ == "__main__":
    main()
