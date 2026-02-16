#!/usr/bin/env python3
"""
Generate a diagnostics support bundle for incident response.

The bundle is intentionally sanitized:
- Includes environment metadata only from an allowlist.
- Redacts credentials from DATABASE_URL.
- Captures bounded log/report snapshots.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "support_bundles"
SAFE_ENV_KEYS = (
    "FLASK_ENV",
    "PORT",
    "BACKEND_PORT",
    "FRONTEND_PORT",
    "DATABASE_URL",
    "SESSION_COOKIE_SECURE",
    "SESSION_COOKIE_SAMESITE",
    "RATELIMIT_STORAGE_URI",
    "LLM_PROVIDER_TIMEOUT_SECONDS",
    "LLM_PROVIDER_MAX_RETRIES",
    "SENTRY_DSN",
    "SENTRY_TRACES_SAMPLE_RATE",
    "SENTRY_PROFILES_SAMPLE_RATE",
)
DEFAULT_ENDPOINTS = (
    ("health", "http://127.0.0.1:5000/health"),
    ("ready", "http://127.0.0.1:5000/ready"),
    ("metrics", "http://127.0.0.1:5000/metrics"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a support diagnostics bundle.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where bundle archive should be written.",
    )
    parser.add_argument(
        "--max-log-bytes",
        type=int,
        default=2_000_000,
        help="Maximum bytes copied per log file.",
    )
    parser.add_argument(
        "--max-files-per-group",
        type=int,
        default=10,
        help="Maximum files copied from logs/ and reports/ groups.",
    )
    parser.add_argument(
        "--skip-http",
        action="store_true",
        help="Skip HTTP probes (/health, /ready, /metrics).",
    )
    parser.add_argument(
        "--skip-runtime-precheck",
        action="store_true",
        help="Skip runtime precheck capture in bundle.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%SZ")
    archive_path = output_dir / f"support_bundle_{timestamp}.zip"

    with tempfile.TemporaryDirectory(prefix="dle_support_bundle_") as tmp_dir:
        bundle_root = Path(tmp_dir) / "support_bundle"
        bundle_root.mkdir(parents=True, exist_ok=True)

        _write_json(bundle_root / "manifest.json", _build_manifest())
        _write_json(bundle_root / "environment_sanitized.json", _safe_environment())
        (bundle_root / "git_snapshot.txt").write_text(_git_snapshot(), encoding="utf-8")
        (bundle_root / "system_snapshot.txt").write_text(_system_snapshot(), encoding="utf-8")

        if not args.skip_runtime_precheck:
            (bundle_root / "runtime_precheck.txt").write_text(_runtime_precheck_output(), encoding="utf-8")

        if not args.skip_http:
            _write_json(bundle_root / "http_probe.json", _http_probe_snapshot())

        _copy_recent_files(
            source_dir=ROOT / "logs",
            target_dir=bundle_root / "logs",
            max_files=args.max_files_per_group,
            max_bytes=args.max_log_bytes,
        )
        _copy_recent_files(
            source_dir=ROOT / "reports",
            target_dir=bundle_root / "reports",
            max_files=args.max_files_per_group,
            max_bytes=args.max_log_bytes,
        )

        with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle_zip:
            for file_path in bundle_root.rglob("*"):
                if file_path.is_file():
                    bundle_zip.write(file_path, file_path.relative_to(bundle_root))

    print(str(archive_path))
    return 0


def _build_manifest() -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "cwd": str(ROOT),
    }


def _safe_environment() -> dict[str, Any]:
    safe_env: dict[str, Any] = {}
    for key in SAFE_ENV_KEYS:
        value = os.environ.get(key)
        if value is None:
            continue
        if key == "DATABASE_URL":
            safe_env[key] = _redact_database_url(value)
            continue
        if key == "SENTRY_DSN":
            safe_env[key] = "***configured***" if value.strip() else ""
            continue
        safe_env[key] = value

    safe_env["provider_keys_configured"] = {
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "AZURE_OPENAI_API_KEY": bool(os.environ.get("AZURE_OPENAI_API_KEY")),
        "GOOGLE_API_KEY": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")),
    }
    return safe_env


def _redact_database_url(database_url: str) -> str:
    try:
        parsed = urlsplit(database_url)
        if not parsed.netloc or "@" not in parsed.netloc:
            return database_url
        auth, host = parsed.netloc.split("@", 1)
        if ":" in auth:
            user, _password = auth.split(":", 1)
            redacted_auth = f"{user}:***"
        else:
            redacted_auth = "***"
        return urlunsplit((parsed.scheme, f"{redacted_auth}@{host}", parsed.path, parsed.query, parsed.fragment))
    except Exception:  # noqa: BLE001
        return "***redacted***"


def _git_snapshot() -> str:
    parts = [
        "$ git rev-parse HEAD",
        _run_command(["git", "rev-parse", "HEAD"]),
        "",
        "$ git status --short",
        _run_command(["git", "status", "--short"]),
        "",
        "$ git branch --show-current",
        _run_command(["git", "branch", "--show-current"]),
    ]
    return "\n".join(parts).strip() + "\n"


def _system_snapshot() -> str:
    parts = [
        "$ python --version",
        _run_command([sys.executable, "--version"]),
        "",
        "$ node --version",
        _run_command(["node", "--version"]),
        "",
        "$ npm --version",
        _run_command(["npm", "--version"]),
    ]
    return "\n".join(parts).strip() + "\n"


def _runtime_precheck_output() -> str:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "runtime_precheck.py"),
        "--skip-ports",
        "--allow-env-from-process",
    ]
    return _run_command(command, max_chars=120_000)


def _http_probe_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {"timestamp": datetime.now(UTC).isoformat(), "endpoints": {}}
    for name, url in DEFAULT_ENDPOINTS:
        snapshot["endpoints"][name] = _probe_http_endpoint(url)
    return snapshot


def _probe_http_endpoint(url: str, timeout_seconds: int = 5) -> dict[str, Any]:
    request = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status_code": int(response.status),
                "headers": dict(response.headers.items()),
                "body_preview": body[:20_000],
            }
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body = ""
        return {"ok": False, "status_code": int(exc.code), "error": str(exc), "body_preview": body[:20_000]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _copy_recent_files(
    *,
    source_dir: Path,
    target_dir: Path,
    max_files: int,
    max_bytes: int,
) -> None:
    if not source_dir.exists() or not source_dir.is_dir():
        return
    files = [path for path in source_dir.rglob("*") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_file in files[: max(0, int(max_files))]:
        relative = source_file.relative_to(source_dir)
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        _copy_bounded(source_file, destination, max_bytes=max_bytes)


def _copy_bounded(source_file: Path, destination: Path, *, max_bytes: int) -> None:
    with source_file.open("rb") as src:
        data = src.read(max(0, int(max_bytes)))
        destination.write_bytes(data)


def _run_command(command: list[str], *, max_chars: int = 50_000) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        output = (completed.stdout or "") + (("\n" + completed.stderr) if completed.stderr else "")
        output = output.strip()
        if not output:
            output = "<no output>"
        if len(output) > max_chars:
            return output[:max_chars] + "\n<truncated>"
        return output
    except Exception as exc:  # noqa: BLE001
        return f"<command failed: {exc}>"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

