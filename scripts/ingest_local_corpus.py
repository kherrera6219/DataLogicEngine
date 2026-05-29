"""Ingest local files/folders into SQL knowledge nodes and Chroma."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def ingest_local_corpus(
    path: str,
    *,
    recursive: bool = True,
    chunk_size: int = 1200,
    source_label: str | None = None,
) -> dict:
    """Run local corpus ingestion inside the Flask app context."""
    import app as app_module
    from backend.ingestion import LocalKnowledgeIngestionService

    with app_module.app.app_context():
        service = LocalKnowledgeIngestionService(chunk_size=chunk_size)
        result = service.ingest_path(
            Path(path),
            recursive=recursive,
            source_label=source_label,
        )
        return result.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="File or directory to ingest.")
    parser.add_argument("--no-recursive", action="store_true", help="Do not recurse into child directories.")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Target chunk size in characters.")
    parser.add_argument("--source-label", default=None, help="Optional display label for generated nodes.")
    args = parser.parse_args()

    result = ingest_local_corpus(
        args.path,
        recursive=not args.no_recursive,
        chunk_size=args.chunk_size,
        source_label=args.source_label,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("files_ingested", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
