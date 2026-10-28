"""Offline long-document chunking candidate; does not modify application data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from backend.services.local_sentence_embedding import LocalSentenceEmbedding
from backend.services.model_text_chunking import model_text_chunks as model_chunks
from backend.services.text_chunking import split_text
from scripts.evaluate_local_retrieval_candidates import cosine
from scripts.probe_offline_embedding_bundle import MANIFEST, WEIGHTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    args = parser.parse_args()
    raw = Path("docs/evaluation/retrieval_qualification_v1.json").read_bytes()
    corpus = json.loads(raw)
    embed = LocalSentenceEmbedding(
        args.model_path,
        expected_weights_sha256=WEIGHTS,
        expected_manifest_sha256=MANIFEST,
    )
    model = embed._load()
    filler = (
        "This fictional handbook also contains general introductory material. "
        "Its repeated introduction explains that headings organize sections and "
        "readers should consult the applicable detailed policy near the end. "
    ) * 30
    results = {}
    for method in ("existing_512_units", "model_token_spans"):
        pieces = []
        for document in corpus["documents"]:
            text = filler + document["text"]
            chunks = (
                split_text(text, 512, 50)
                if method == "existing_512_units"
                else model_chunks(text, model.tokenizer, model.max_seq_length)
            )
            pieces.extend((document["id"], chunk) for chunk in chunks)
        tokens = [
            len(
                model.tokenizer(text, add_special_tokens=True, truncation=False)[
                    "input_ids"
                ]
            )
            for _, text in pieces
        ]
        vectors = [embed(text) for _, text in pieces]
        rows = []
        for document in corpus["documents"]:
            for query in document["held_out"]:
                vector = embed(query)
                scores = [cosine(vector, target) for target in vectors]
                order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:4]
                rows.append(
                    {
                        "query": query,
                        "expected": document["id"],
                        "top4": [[pieces[i][0], scores[i]] for i in order],
                        "retained": any(
                            pieces[i][0] == document["id"] and scores[i] >= 0.25
                            for i in order
                        ),
                    }
                )
        results[method] = {
            "pieces": len(pieces),
            "max_input_tokens": max(tokens),
            "pieces_over_model_limit": sum(
                count > model.max_seq_length for count in tokens
            ),
            "retained_at_cosine_025": sum(row["retained"] for row in rows),
            "total": len(rows),
            "cases": rows,
        }
    print(
        json.dumps(
            {
                "status": "candidate_not_activated",
                "model_limit": model.max_seq_length,
                "corpus_sha256": hashlib.sha256(raw).hexdigest(),
                "script_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
                "chunker_sha256": hashlib.sha256(
                    Path("backend/services/model_text_chunking.py").read_bytes()
                ).hexdigest(),
                "model_manifest_sha256": MANIFEST,
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
