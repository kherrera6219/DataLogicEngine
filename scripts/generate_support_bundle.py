#!/usr/bin/env python3
"""Preview or generate a redacted local diagnostics support bundle."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.observability.support_bundle import (  # noqa: E402
    SupportBundleBuilder,
    SupportBundleOptions,
)

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "support_bundles"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a support diagnostics bundle.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where the bundle archive should be written.",
    )
    parser.add_argument(
        "--max-log-bytes",
        type=int,
        default=2_000_000,
        help="Maximum bytes copied and redacted per approved log file.",
    )
    parser.add_argument(
        "--max-files-per-group",
        type=int,
        default=10,
        help="Maximum approved log files included.",
    )
    parser.add_argument(
        "--skip-http",
        action="store_true",
        help="Skip local HTTP probes.",
    )
    parser.add_argument(
        "--skip-runtime-precheck",
        action="store_true",
        help="Skip runtime precheck capture.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the exact redacted file inventory without creating an archive.",
    )
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt the archive with an interactively entered passphrase.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.preview and args.encrypt:
        raise SystemExit("--preview and --encrypt cannot be combined")

    options = SupportBundleOptions(
        max_log_bytes=args.max_log_bytes,
        max_log_files=args.max_files_per_group,
        include_http=not args.skip_http,
        include_runtime_precheck=not args.skip_runtime_precheck,
    )
    builder = SupportBundleBuilder(ROOT)
    if args.preview:
        print(json.dumps(builder.preview(options=options), indent=2, ensure_ascii=True))
        return 0

    passphrase = None
    if args.encrypt:
        passphrase = getpass.getpass("Support bundle encryption passphrase: ")
        confirmation = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirmation:
            raise SystemExit("support bundle encryption passphrases did not match")

    result = builder.export(
        args.output_dir,
        options=options,
        encryption_passphrase=passphrase,
    )
    print(result["archive_path"])
    print(result["sidecar_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
