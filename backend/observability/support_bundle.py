"""Previewable, redacted, hashed local support-bundle generation."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from backend.observability.redaction import redact_text, redact_value

SUPPORT_BUNDLE_SCHEMA = "dle.support-bundle.v1"
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
    "DLE_EXTERNAL_TELEMETRY_ENABLED",
)
URL_ENV_KEYS = {"DATABASE_URL", "RATELIMIT_STORAGE_URI"}
SAFE_HTTP_HEADERS = {
    "content-type",
    "retry-after",
    "x-correlation-id",
    "x-request-id",
    "x-crash-id",
}
SAFE_LOG_SUFFIXES = {".log", ".jsonl", ".txt"}
DEFAULT_ENDPOINTS = (
    ("health", "http://127.0.0.1:5000/health"),
    ("ready", "http://127.0.0.1:5000/ready"),
    ("metrics", "http://127.0.0.1:5000/metrics"),
)
CONTENT_VALUE_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9_])"
    r"(?P<prefix>[\"']?(?:prompt|document|content|response|provider[_-]?payload|request[_-]?body)"
    r"[\"']?\s*[:=]\s*)"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^\r\n,;]+)"
)


@dataclass(frozen=True)
class SupportBundleOptions:
    """Bounded inputs for preview/export."""

    max_log_bytes: int = 2_000_000
    max_log_files: int = 10
    include_http: bool = False
    include_runtime_precheck: bool = False

    def validate(self) -> None:
        if self.max_log_bytes < 1:
            raise ValueError("max_log_bytes_must_be_positive")
        if self.max_log_files < 0:
            raise ValueError("max_log_files_must_be_non_negative")
        if self.max_log_bytes > 10_000_000:
            raise ValueError("max_log_bytes_exceeds_support_limit")
        if self.max_log_files > 50:
            raise ValueError("max_log_files_exceeds_support_limit")


class SupportBundleBuilder:
    """Build the exact same staged contract for preview and export."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def preview(
        self,
        *,
        options: SupportBundleOptions | None = None,
        diagnostics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        active_options = options or SupportBundleOptions()
        active_options.validate()
        with tempfile.TemporaryDirectory(prefix="dle_support_preview_") as tmp_dir:
            bundle_root = Path(tmp_dir) / "support_bundle"
            files = self._stage(bundle_root, active_options, diagnostics=diagnostics)
            return {
                "schema_version": SUPPORT_BUNDLE_SCHEMA,
                "mode": "preview",
                "archive_created": False,
                "content_policy": "redacted_diagnostics_only",
                "user_content_included": False,
                "files": files,
            }

    def export(
        self,
        output_dir: str | Path,
        *,
        options: SupportBundleOptions | None = None,
        diagnostics: dict[str, Any] | None = None,
        encryption_passphrase: str | None = None,
    ) -> dict[str, Any]:
        active_options = options or SupportBundleOptions()
        active_options.validate()
        destination = Path(output_dir).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        purge_support_directory(destination)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%fZ")
        archive_path = destination / f"support_bundle_{timestamp}.zip"

        with tempfile.TemporaryDirectory(prefix="dle_support_bundle_") as tmp_dir:
            bundle_root = Path(tmp_dir) / "support_bundle"
            files = self._stage(bundle_root, active_options, diagnostics=diagnostics)
            with zipfile.ZipFile(
                archive_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as bundle_zip:
                for file_path in sorted(path for path in bundle_root.rglob("*") if path.is_file()):
                    bundle_zip.write(file_path, file_path.relative_to(bundle_root))

        final_path = archive_path
        encrypted = False
        if encryption_passphrase is not None:
            if len(encryption_passphrase) < 12:
                archive_path.unlink(missing_ok=True)
                raise ValueError("support_bundle_passphrase_too_short")
            final_path = encrypt_archive(archive_path, encryption_passphrase)
            encrypted = True

        digest = sha256_file(final_path)
        sidecar = final_path.with_name(f"{final_path.name}.sha256")
        sidecar.write_text(f"{digest}  {final_path.name}\n", encoding="ascii")
        purge_support_directory(destination)
        return {
            "schema_version": SUPPORT_BUNDLE_SCHEMA,
            "archive_path": str(final_path),
            "sidecar_path": str(sidecar),
            "sha256": digest,
            "size_bytes": final_path.stat().st_size,
            "encrypted": encrypted,
            "files": files,
        }

    def _stage(
        self,
        bundle_root: Path,
        options: SupportBundleOptions,
        *,
        diagnostics: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        bundle_root.mkdir(parents=True, exist_ok=True)
        write_json(bundle_root / "manifest.json", self._build_manifest())
        write_json(bundle_root / "environment_sanitized.json", safe_environment())
        write_json(bundle_root / "source_snapshot.json", self._source_snapshot())
        write_json(bundle_root / "system_snapshot.json", system_snapshot())
        write_json(bundle_root / "resource_snapshot.json", resource_snapshot(self.root))
        if diagnostics is not None:
            write_json(bundle_root / "diagnostics.json", diagnostics)
        if options.include_runtime_precheck:
            (bundle_root / "runtime_precheck.txt").write_text(
                redact_support_text(self._runtime_precheck_output()),
                encoding="utf-8",
            )
        if options.include_http:
            write_json(bundle_root / "http_probe.json", http_probe_snapshot())
        copy_recent_redacted_logs(
            source_dir=self.root / "logs",
            target_dir=bundle_root / "logs",
            max_files=options.max_log_files,
            max_bytes=options.max_log_bytes,
        )
        return write_file_inventory(bundle_root)

    def _build_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": SUPPORT_BUNDLE_SCHEMA,
            "generated_at": datetime.now(UTC).isoformat(),
            "device_id_hash": hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()[:16],
            "product_version": os.environ.get("APP_VERSION", "0.1.1"),
            "content_policy": "redacted_diagnostics_only",
            "user_content_included": False,
            "external_telemetry_required": False,
        }

    def _source_snapshot(self) -> dict[str, Any]:
        commit = run_command(["git", "rev-parse", "HEAD"], cwd=self.root).strip()
        dirty_probe = run_command(["git", "status", "--porcelain"], cwd=self.root).strip()
        return {
            "commit": commit if re.fullmatch(r"[0-9a-f]{40}", commit) else "unavailable",
            "working_tree_dirty": dirty_probe not in {"", "<no output>"},
        }

    def _runtime_precheck_output(self) -> str:
        script_path = self.root / "scripts" / "runtime_precheck.py"
        if not script_path.is_file():
            return "runtime precheck is unavailable in this installation"
        return run_command(
            [
                sys.executable,
                str(script_path),
                "--skip-ports",
                "--allow-env-from-process",
            ],
            cwd=self.root,
            max_chars=120_000,
        )


def safe_environment() -> dict[str, Any]:
    safe_env: dict[str, Any] = {}
    for key in SAFE_ENV_KEYS:
        value = os.environ.get(key)
        if value is None:
            continue
        if key in URL_ENV_KEYS:
            safe_env[key] = redact_service_url(value)
        elif key == "SENTRY_DSN":
            safe_env[key] = "***configured***" if value.strip() else ""
        else:
            safe_env[key] = value
    safe_env["provider_keys_configured"] = {
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "google": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")),
    }
    return safe_env


def redact_service_url(service_url: str) -> str:
    try:
        parsed = urlsplit(service_url)
        if not parsed.scheme:
            return "***configured***" if service_url.strip() else ""
        host = parsed.hostname or "local"
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except Exception:  # noqa: BLE001
        return "***redacted***"


def system_snapshot() -> dict[str, Any]:
    return {
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python": run_command([sys.executable, "--version"]),
        "node": run_command(["node", "--version"]),
        "npm": run_command(["npm", "--version"]),
    }


def resource_snapshot(root: Path) -> dict[str, Any]:
    disk = shutil.disk_usage(root)
    snapshot: dict[str, Any] = {
        "cpu_count": os.cpu_count(),
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
    }
    try:
        import psutil

        memory = psutil.virtual_memory()
        process = psutil.Process()
        snapshot.update(
            {
                "memory_total_bytes": int(memory.total),
                "memory_available_bytes": int(memory.available),
                "process_rss_bytes": int(process.memory_info().rss),
                "process_thread_count": int(process.num_threads()),
            }
        )
    except Exception:  # noqa: BLE001
        snapshot["extended_metrics"] = "unavailable"
    return snapshot


def http_probe_snapshot() -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "endpoints": {name: probe_http_endpoint(url) for name, url in DEFAULT_ENDPOINTS},
    }


def probe_http_endpoint(url: str, timeout_seconds: int = 5) -> dict[str, Any]:
    request = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status_code": int(response.status),
                "headers": safe_http_headers(dict(response.headers.items())),
                "body_preview": redact_support_text(body[:20_000]),
            }
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body = ""
        return {
            "ok": False,
            "status_code": int(exc.code),
            "error": redact_support_text(str(exc)),
            "body_preview": redact_support_text(body[:20_000]),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": redact_support_text(str(exc))}


def copy_recent_redacted_logs(
    *,
    source_dir: Path,
    target_dir: Path,
    max_files: int,
    max_bytes: int,
) -> None:
    if not source_dir.is_dir():
        return
    files = [
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SAFE_LOG_SUFFIXES
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_file in files[:max_files]:
        destination = target_dir / source_file.relative_to(source_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source_file.open("rb") as source:
            data = source.read(max_bytes)
        destination.write_text(
            redact_support_text(data.decode("utf-8", errors="replace")),
            encoding="utf-8",
        )


def redact_support_text(value: str) -> str:
    redacted = redact_text(str(value))
    redacted = CONTENT_VALUE_PATTERN.sub(
        lambda match: f"{match.group('prefix')}[REDACTED_USER_CONTENT]",
        redacted,
    )
    return re.sub(
        r"(?i)(?:[A-Z]:\\Users\\|/home/|/Users/)[^\\/\s]+",
        "[REDACTED_USER_HOME]",
        redacted,
    )


def safe_http_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key.lower(): redact_support_text(value)
        for key, value in headers.items()
        if key.lower() in SAFE_HTTP_HEADERS
    }


def write_file_inventory(bundle_root: Path) -> list[dict[str, Any]]:
    entries = [
        {
            "path": file_path.relative_to(bundle_root).as_posix(),
            "size_bytes": file_path.stat().st_size,
            "sha256": sha256_file(file_path),
            "classification": "redacted_diagnostics",
        }
        for file_path in sorted(path for path in bundle_root.rglob("*") if path.is_file())
    ]
    write_json(bundle_root / "files.json", entries)
    return entries


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def purge_support_directory(
    destination: Path,
    *,
    max_archives: int = 5,
    max_total_bytes: int = 100 * 1024 * 1024,
) -> None:
    """Bound app-owned support artifacts without touching unrelated files."""
    archive_pattern = re.compile(
        r"^support_bundle_\d{8}_\d{6}_\d{6}Z\.zip(?:\.enc)?$"
    )
    archives = sorted(
        (
            path
            for path in destination.iterdir()
            if path.is_file() and archive_pattern.fullmatch(path.name)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    retained_bytes = 0
    for index, path in enumerate(archives):
        size = path.stat().st_size
        retain = index < max_archives and retained_bytes + size <= max_total_bytes
        if retain:
            retained_bytes += size
            continue
        path.unlink(missing_ok=True)
        path.with_name(f"{path.name}.sha256").unlink(missing_ok=True)


def encrypt_archive(archive_path: Path, passphrase: str) -> Path:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = os.urandom(16)
    nonce = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)
    key = kdf.derive(passphrase.encode("utf-8"))
    envelope = {
        "schema_version": "dle.support-bundle.encrypted.v1",
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": 600_000,
        "cipher": "AES-256-GCM",
        "salt_hex": salt.hex(),
        "nonce_hex": nonce.hex(),
    }
    header = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("ascii")
    ciphertext = AESGCM(key).encrypt(nonce, archive_path.read_bytes(), header)
    encrypted_path = archive_path.with_suffix(f"{archive_path.suffix}.enc")
    encrypted_path.write_bytes(b"DLE-SUPPORT-BUNDLE-ENC-V1\n" + header + b"\n" + ciphertext)
    archive_path.unlink()
    return encrypted_path


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    max_chars: int = 50_000,
) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        output = (completed.stdout or "") + (("\n" + completed.stderr) if completed.stderr else "")
        output = output.strip() or "<no output>"
        return output[:max_chars] + ("\n<truncated>" if len(output) > max_chars else "")
    except Exception as exc:  # noqa: BLE001
        return f"<command failed: {redact_support_text(str(exc))}>"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_value(payload), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
