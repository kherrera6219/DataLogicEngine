"""CLI interface for running dataset exports across parallel workers."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from .exporter_core import DatasetExporter
from .privacy_redactor import SecurityError

logger = logging.getLogger(__name__)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load caller-supplied trace dictionaries without manufacturing training evidence."""
    traces: list[dict[str, Any]] = []
    with path.resolve().open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"Input line {line_number} must contain a JSON object.")
            traces.append(value)
    return traces


def main() -> None:
    """CLI entry point for dataset exporter with error handling and non-zero exit codes."""
    parser = argparse.ArgumentParser(description="DataLogicEngine Training Dataset Exporter")
    parser.add_argument("--type", choices=["sft", "dpo", "prm"], default="sft", help="Export dataset type")
    parser.add_argument("--format", choices=["parquet", "jsonl"], default="parquet", help="Output serialization format")
    parser.add_argument("--min-confidence", type=float, default=0.98, help="Minimum confidence threshold for export")
    parser.add_argument("--out", type=str, default="./datasets/export.parquet", help="Output file path")
    parser.add_argument("--input-jsonl", type=Path, required=True, help="JSONL file containing governed trace records")
    parser.add_argument("--worker-id", type=int, default=1, help="Worker VM index for sharded filenames")

    args = parser.parse_args()

    try:
        traces = _read_jsonl(args.input_jsonl)

        out_path = Path(args.out)
        if args.worker_id > 1:
            out_path = out_path.with_name(f"{out_path.stem}_worker_{args.worker_id}{out_path.suffix}")

        result = DatasetExporter.export_dataset(
            traces=traces,
            export_type=args.type,
            output_path=out_path,
            min_confidence=args.min_confidence,
            format_type=args.format,
            base_dir=out_path.parent,
        )

        print(json.dumps(result, indent=2))

    except SecurityError as exc:
        logger.critical("Dataset export blocked due to security violation: %s", exc)
        print(json.dumps({"status": "error", "error_type": "SecurityError", "message": str(exc)}), file=sys.stderr)
        sys.exit(2)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        logger.error("Dataset export failed: %s", exc)
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
