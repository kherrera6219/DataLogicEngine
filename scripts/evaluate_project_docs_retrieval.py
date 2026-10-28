"""Screen local retrieval on public project documentation without changing data.

This small, manually labeled screen is not customer-data or acceptance evidence.
The caller supplies an existing, fingerprinted offline model directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from time import perf_counter

from backend.services.local_sentence_embedding import LocalSentenceEmbedding
from backend.services.rag_service import RAGService
from backend.services.text_chunking import split_text
from scripts.evaluate_local_retrieval_candidates import cosine, lexical_similarity

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (
        "USER_GUIDE.md",
        "2. Start governed AI chat",
        "How do I ask the assistant a question?",
    ),
    (
        "USER_GUIDE.md",
        "3. Approve a Client Gateway application",
        "How do I authorize a client to use the gateway?",
    ),
    (
        "USER_GUIDE.md",
        "4. Review Knowledge Algorithms",
        "Where can I inspect the knowledge algorithms?",
    ),
    (
        "USER_GUIDE.md",
        "6. Review traces and evidence",
        "How do I examine sources and trace details?",
    ),
    (
        "USER_GUIDE.md",
        "7. Explore graph and knowledge data",
        "Where can I view knowledge graph relationships?",
    ),
    ("USER_GUIDE.md", "8. Run simulations", "How can I start a bounded simulation?"),
    (
        "USER_GUIDE.md",
        "10. Manage MCP connectors",
        "How do I control external MCP tools?",
    ),
    (
        "USER_GUIDE.md",
        "13. Review provider usage and offline replay",
        "Where can I check my provider usage and queued requests?",
    ),
    ("ADMINISTRATOR_OPERATIONS_GUIDE.md", "Backup", "How are local backups created?"),
    (
        "ADMINISTRATOR_OPERATIONS_GUIDE.md",
        "Restore and disaster recovery",
        "What is the process for restoring a backup?",
    ),
    (
        "ADMINISTRATOR_OPERATIONS_GUIDE.md",
        "Retention and deletion",
        "How does the administrator handle retention and data deletion?",
    ),
    (
        "ADMINISTRATOR_OPERATIONS_GUIDE.md",
        "Incident response",
        "What steps should the operator take when an incident occurs?",
    ),
)
UNRELATED_QUESTIONS = (
    "How do I bake a sourdough loaf?",
    "What is the orbit of Jupiter?",
    "How do I replace a bicycle tire?",
    "Which plants grow in a desert?",
    "What are the rules of chess castling?",
    "How do I tune a violin?",
    "What causes a volcanic eruption?",
    "How do I make a wool sweater?",
)
SCREEN_THRESHOLDS = (0.15, 0.0, -0.25, -0.5)


def section(filename: str, heading: str) -> str:
    """Read the named section from the checked-in public documentation."""
    contents = (ROOT / "docs" / filename).read_text(encoding="utf-8")
    marker = re.search(r"^#{2,3}\s+" + re.escape(heading) + r"\s*$", contents, re.M)
    if marker is None:
        raise ValueError(f"public_document_heading_missing: {filename}: {heading}")
    level = len(marker.group(0)) - len(marker.group(0).lstrip("#"))
    following = re.search(
        r"^#{1," + str(level) + r"}\s+", contents[marker.end() :], re.M
    )
    end = marker.end() + following.start() if following else len(contents)
    return contents[marker.start() : end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--weights-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--chunked", action="store_true", help="Screen production-style document chunks"
    )
    args = parser.parse_args()
    embed = LocalSentenceEmbedding(
        args.model_path.resolve(strict=True),
        expected_weights_sha256=args.weights_sha256,
        expected_manifest_sha256=args.manifest_sha256,
    )
    started = perf_counter()
    sections = [section(filename, heading) for filename, heading, _ in CASES]
    documents: list[str] = []
    source_ids: list[int] = []
    for source_id, text in enumerate(sections):
        chunks = split_text(text, 512, 50) if args.chunked else [text]
        documents.extend(chunks)
        source_ids.extend([source_id] * len(chunks))
    semantic_documents = [embed(document) for document in documents]
    semantic_questions = [embed(question) for _, _, question in CASES]
    unrelated_vectors = [embed(question) for question in UNRELATED_QUESTIONS]
    baseline = RAGService()
    hash_documents = [
        baseline._deterministic_embedding(document) for document in documents
    ]
    counts = {name: [0, 0, 0] for name in ("hash", "lexical", "minilm")}
    positive_retained = {threshold: 0 for threshold in SCREEN_THRESHOLDS}
    for index, (_, _, question) in enumerate(CASES):
        query_hash = baseline._deterministic_embedding(question)
        scores = {
            "hash": [cosine(query_hash, item) for item in hash_documents],
            "lexical": [lexical_similarity(question, item) for item in documents],
            "minilm": [
                cosine(semantic_questions[index], item) for item in semantic_documents
            ],
        }
        for name, values in scores.items():
            ordered = sorted(range(len(values)), key=lambda item: (-values[item], item))
            counts[name][0] += source_ids[ordered[0]] == index
            counts[name][1] += any(source_ids[item] == index for item in ordered[:4])
            if name != "lexical":
                query = query_hash if name == "hash" else semantic_questions[index]
                vectors = hash_documents if name == "hash" else semantic_documents
                l2_scores = [
                    1.0 - sum((a - b) ** 2 for a, b in zip(query, target))
                    for target in vectors
                ]
                l2_ordered = sorted(
                    range(len(l2_scores)), key=lambda item: (-l2_scores[item], item)
                )
                counts[name][2] += any(
                    source_ids[item] == index and l2_scores[item] >= 0.15
                    for item in l2_ordered[:4]
                )
                if name == "minilm":
                    for threshold in SCREEN_THRESHOLDS:
                        positive_retained[threshold] += any(
                            source_ids[item] == index and l2_scores[item] >= threshold
                            for item in l2_ordered[:4]
                        )
    print(
        f"Public documentation screen: {len(CASES)} sections, "
        f"{len(documents)} indexed pieces and {len(CASES)} questions"
    )
    for name, (top1, top4, retained) in counts.items():
        suffix = "not applicable" if name == "lexical" else f"{retained}/{len(CASES)}"
        print(
            f"{name}: top1={top1}/{len(CASES)} top4={top4}/{len(CASES)} threshold={suffix}"
        )
    negative_scores = [
        max(
            1.0 - sum((a - b) ** 2 for a, b in zip(question, document))
            for document in semantic_documents
        )
        for question in unrelated_vectors
    ]
    for threshold in SCREEN_THRESHOLDS:
        admitted = sum(score >= threshold for score in negative_scores)
        print(
            f"minilm threshold {threshold:.2f}: "
            f"known target retained={positive_retained[threshold]}/{len(CASES)}, "
            f"unrelated query with a match={admitted}/{len(UNRELATED_QUESTIONS)}"
        )
    print(f"Elapsed: {perf_counter() - started:.2f}s; model truncation applies")
    print(
        "Screening only: no customer data, threshold qualification or migration claim."
    )


if __name__ == "__main__":
    main()
