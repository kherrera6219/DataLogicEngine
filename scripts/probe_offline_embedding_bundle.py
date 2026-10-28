"""Probe the existing offline model in a separate source/frozen process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys
from time import perf_counter
from unittest.mock import patch

from backend.services.local_sentence_embedding import LocalSentenceEmbedding

WEIGHTS = "53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db"
MANIFEST = "8c4ccf957588dbe5df32048c58a29a8e81fd46e3fa8d940e8d7777b348b0c979"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path)
    args = parser.parse_args()
    model_path = args.model_path
    if model_path is None:
        if not getattr(sys, "frozen", False):
            parser.error("--model-path is required outside the frozen probe")
        model_path = Path(sys._MEIPASS) / "offline-model"
    attempts = []

    def denied(*args, **kwargs):
        attempts.append("blocked")
        raise RuntimeError("offline_probe_network_denied")

    started = perf_counter()
    with (
        patch.object(socket.socket, "connect", denied),
        patch.object(socket.socket, "connect_ex", denied),
        patch.object(socket, "create_connection", denied),
    ):
        embed = LocalSentenceEmbedding(
            model_path,
            expected_weights_sha256=WEIGHTS,
            expected_manifest_sha256=MANIFEST,
        )
        query = embed("How long are nightly backups kept?")
        positive = embed(
            "Encrypted backups are created nightly and retained for ninety days."
        )
        negative = embed("The violin has four strings tuned in fifths.")
    if attempts:
        raise RuntimeError("offline_probe_network_attempted")
    positive_score = sum(a * b for a, b in zip(query, positive))
    negative_score = sum(a * b for a, b in zip(query, negative))
    if len(query) != 384 or positive_score <= negative_score:
        raise RuntimeError("offline_probe_ranking_failed")
    print(
        json.dumps(
            {
                "status": "pass",
                "frozen": bool(getattr(sys, "frozen", False)),
                "dimensions": len(query),
                "network_attempts": len(attempts),
                "positive_cosine": positive_score,
                "negative_cosine": negative_score,
                "seconds": perf_counter() - started,
            }
        )
    )


if __name__ == "__main__":
    main()
