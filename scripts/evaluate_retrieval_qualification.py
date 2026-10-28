"""Measure an owner-review candidate corpus offline; never activate an index."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from backend.services.local_sentence_embedding import LocalSentenceEmbedding
from backend.services.rag_service import RAGService
from backend.services.text_chunking import split_text
from scripts.evaluate_local_retrieval_candidates import cosine, lexical_similarity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--weights-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("docs/evaluation/retrieval_qualification_v1.json"),
    )
    args = parser.parse_args()
    raw = args.corpus.read_bytes()
    corpus = json.loads(raw)
    embed = LocalSentenceEmbedding(
        args.model_path,
        expected_weights_sha256=args.weights_sha256,
        expected_manifest_sha256=args.manifest_sha256,
    )
    documents = corpus["documents"]
    pieces = [
        (item["id"], chunk)
        for item in documents
        for chunk in split_text(item["text"], 512, 50)
    ]
    start = perf_counter()
    vectors = [embed(text) for _, text in pieces]
    cold_seconds = perf_counter() - start
    baseline = RAGService()
    hashes = [baseline._deterministic_embedding(text) for _, text in pieces]
    timings = []
    results = {name: [] for name in ("calibration", "held_out", "unrelated")}
    for partition in results:
        queries = (
            [(None, query) for query in corpus["unrelated_queries"]]
            if partition == "unrelated"
            else [
                (item["id"], query)
                for item in documents
                for query in (
                    [item["calibration"]]
                    if partition == "calibration"
                    else item["held_out"]
                )
            ]
        )
        for expected, query in queries:
            start = perf_counter()
            vector = embed(query)
            semantic = [cosine(vector, target) for target in vectors]
            timings.append(perf_counter() - start)
            hashed = baseline._deterministic_embedding(query)
            scores = {
                "minilm": semantic,
                "hash": [cosine(hashed, target) for target in hashes],
                "lexical": [lexical_similarity(query, text) for _, text in pieces],
            }
            rankings = {
                name: sorted(range(len(values)), key=lambda i: (-values[i], i))
                for name, values in scores.items()
            }
            # Equal-weight reciprocal-rank fusion: no unqualified scale mixing.
            hybrid = [
                sum(
                    1.0 / (60 + rankings[name].index(i) + 1)
                    for name in ("minilm", "lexical")
                )
                for i in range(len(pieces))
            ]
            rankings["hybrid"] = sorted(
                range(len(hybrid)), key=lambda i: (-hybrid[i], i)
            )
            results[partition].append(
                {
                    "query": query,
                    "expected": expected,
                    "top4": {
                        name: [pieces[i][0] for i in order[:4]]
                        for name, order in rankings.items()
                    },
                    "semantic_top4_scores": [
                        [pieces[i][0], semantic[i]] for i in rankings["minilm"][:4]
                    ],
                }
            )
    summary = {}
    for partition in ("calibration", "held_out"):
        rows = results[partition]
        summary[partition] = {
            name: {
                "top1": sum(row["top4"][name][0] == row["expected"] for row in rows),
                "top4": sum(row["expected"] in row["top4"][name] for row in rows),
                "total": len(rows),
            }
            for name in ("hash", "lexical", "minilm", "hybrid")
        }
    thresholds = {}
    for threshold in (0.15, 0.25, 0.35, 0.45, 0.55):
        thresholds[str(threshold)] = {
            partition: sum(
                any(
                    doc == row["expected"] and score >= threshold
                    for doc, score in row["semantic_top4_scores"]
                )
                for row in results[partition]
            )
            for partition in ("calibration", "held_out")
        }
        thresholds[str(threshold)]["unrelated_matches"] = sum(
            row["semantic_top4_scores"][0][1] >= threshold
            for row in results["unrelated"]
        )
    print(
        json.dumps(
            {
                "status": "candidate_screen_not_acceptance",
                "model_weights_sha256": args.weights_sha256,
                "model_manifest_sha256": args.manifest_sha256,
                "script_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
                "packages": {
                    name: version(name)
                    for name in ("sentence-transformers", "torch", "transformers")
                },
                "metric": "cosine similarity of normalized vectors; warm timing includes query encoding and semantic ranking only",
                "corpus_sha256": hashlib.sha256(raw).hexdigest(),
                "pieces": len(pieces),
                "cold_encode_corpus_seconds": cold_seconds,
                "warm_query_p95_seconds": quantiles(timings, n=100)[94],
                "summary": summary,
                "cosine_thresholds": thresholds,
                "cases": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
