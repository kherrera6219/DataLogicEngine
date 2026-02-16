"""
Runtime environment precheck for the DataLogicEngine stack.

This script surfaces blocking issues that prevent the backend (Flask) and frontend (Next.js)
from starting and communicating locally. It focuses on developer default ports (backend 5000,
frontend 3000), required configuration files, and bootstrap dependency manifests.
"""
import argparse
import json
import os
import sys
import socket
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values

BACKEND_PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 5000)))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", 3000))
ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    level: str
    message: str


def header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def check_python() -> list[CheckResult]:
    header("Python environment")
    results: list[CheckResult] = []

    major, minor = sys.version_info[:2]
    print(f"Detected Python: {major}.{minor}")
    if major < 3 or (major == 3 and minor < 11):
        results.append(CheckResult("BLOCKER", "Python 3.11+ required for parity with dependencies."))
    else:
        results.append(CheckResult("OK", "Python version meets minimum requirement (3.11+)."))

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        results.append(CheckResult("OK", f"Using virtualenv: {venv}"))
    else:
        results.append(CheckResult("WARN", "Not running inside a virtual environment; recreate per README to avoid dependency conflicts."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def check_node() -> list[CheckResult]:
    header("Node.js environment")
    results: list[CheckResult] = []

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if not node_path:
        results.append(CheckResult("BLOCKER", "Node.js not found. Install Node 20.x to run the frontend."))
        for item in results:
            print(f"[{item.level}] {item.message}")
        return results

    results.append(CheckResult("OK", f"node found at {node_path}"))
    if not npm_path:
        results.append(CheckResult("BLOCKER", "npm not found. Install Node.js with npm included."))
    else:
        results.append(CheckResult("OK", f"npm found at {npm_path}"))

    frontend_dir = ROOT / "frontend" / "node_modules"
    if not frontend_dir.exists():
        results.append(CheckResult("ACTION", "Run `cd frontend && npm install` to install frontend dependencies."))
    else:
        results.append(CheckResult("OK", "Frontend dependencies directory detected."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def check_env_files(*, allow_env_from_process: bool = False) -> list[CheckResult]:
    header("Configuration files")
    results: list[CheckResult] = []
    env_files = [ROOT / ".env", ROOT / "config.env"]
    existing = [path for path in env_files if path.exists()]
    if not existing:
        if allow_env_from_process:
            results.append(
                CheckResult(
                    "INFO",
                    "Missing .env/config.env in workspace. Process environment overrides are being used instead.",
                )
            )
        else:
            results.append(CheckResult("BLOCKER", "Missing .env or config.env. Copy .env.template to .env and adjust secrets."))
    else:
        for path in existing:
            results.append(CheckResult("OK", f"Found {path.name} at {path}"))

    env_values: dict[str, str | None] = {}
    for path in existing:
        env_values.update(dotenv_values(path))
    env_values.update({key: value for key, value in os.environ.items()})

    database_url = str(env_values.get("DATABASE_URL") or "").strip()
    sqlite_path = ROOT / "ukg_database.db"
    if sqlite_path.exists():
        results.append(CheckResult("OK", f"SQLite database file present at {sqlite_path}"))
    else:
        if database_url and not database_url.startswith("sqlite:///ukg_database.db"):
            results.append(
                CheckResult(
                    "INFO",
                    f"SQLite file not required because DATABASE_URL is configured as '{database_url}'.",
                )
            )
        else:
            results.append(
                CheckResult(
                    "ACTION",
                    "Initialize local schema via `scripts/windows/start_local_stack.ps1` (it handles migration stamping for local SQLite).",
                )
            )

    required_keys = ("SESSION_SECRET",)
    missing_keys = [key for key in required_keys if not env_values.get(key)]
    if missing_keys:
        missing_display = ", ".join(missing_keys)
        results.append(
            CheckResult(
                "ACTION",
                f"Missing recommended configuration values: {missing_display}. Populate them in .env for stable startup.",
            )
        )

    if not env_values.get("DATABASE_URL"):
        results.append(
            CheckResult(
                "ACTION",
                "DATABASE_URL is not set. Local SQLite fallback is supported, but set DATABASE_URL explicitly for parity.",
            )
        )

    provider_keys = (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "anthropic_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "MISTRAL_API_KEY",
    )
    if not any(env_values.get(key) for key in provider_keys):
        results.append(
            CheckResult(
                "ACTION",
                "No LLM provider key detected. Set at least one provider key for chat/runtime features.",
            )
        )

    flask_env = (env_values.get("FLASK_ENV") or "").strip().lower()
    if flask_env == "production":
        results.append(
            CheckResult(
                "WARN",
                "FLASK_ENV=production detected. For local HTTP development, use FLASK_ENV=development.",
            )
        )

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def check_ports() -> list[CheckResult]:
    header("Port availability")
    results: list[CheckResult] = []
    for label, port in ("Backend", BACKEND_PORT), ("Frontend", FRONTEND_PORT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            if result == 0:
                results.append(CheckResult("BLOCKER", f"{label} port {port} is already in use. Stop the process or choose a different port."))
            else:
                results.append(CheckResult("OK", f"{label} port {port} is free."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def check_templates_and_static() -> list[CheckResult]:
    header("Backend templates & static assets")
    results: list[CheckResult] = []
    templates_dir = ROOT / "templates"
    static_dir = ROOT / "static"
    if templates_dir.exists():
        results.append(CheckResult("OK", f"Templates directory located at {templates_dir}"))
    else:
        results.append(
            CheckResult(
                "WARN",
                "templates/ directory missing; legacy server-rendered pages may be unavailable.",
            )
        )

    if static_dir.exists():
        results.append(CheckResult("OK", f"Static assets directory located at {static_dir}"))
    else:
        results.append(CheckResult("WARN", "static/ directory missing; some assets may not load."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def check_backend_dependencies() -> list[CheckResult]:
    header("Backend dependencies")
    results: list[CheckResult] = []
    req_file = ROOT / "requirements.txt"
    pyproject_file = ROOT / "pyproject.toml"
    uv_lock = ROOT / "uv.lock"

    if req_file.exists():
        results.append(CheckResult("OK", f"requirements.txt found at {req_file}"))
        results.append(CheckResult("INFO", "Install with `pip install -r requirements.txt`."))
    elif pyproject_file.exists():
        results.append(CheckResult("WARN", "requirements.txt missing; fallback manifest pyproject.toml detected."))
        if uv_lock.exists():
            results.append(CheckResult("INFO", "Install with `uv sync` to honor uv.lock."))
        else:
            results.append(CheckResult("INFO", "Install with `pip install -e .` from repository root."))
    else:
        results.append(CheckResult("BLOCKER", "No dependency manifest found (requirements.txt or pyproject.toml)."))

    venv_dir = ROOT / ".venv"
    if venv_dir.exists():
        results.append(CheckResult("OK", "Virtual environment directory detected at .venv."))
    else:
        results.append(CheckResult("WARN", "No .venv folder detected; create one to isolate dependencies."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Runtime environment precheck for DataLogicEngine.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat ACTION-level findings as failures.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Treat WARN-level findings as failures (in addition to strict levels).",
    )
    parser.add_argument(
        "--skip-ports",
        action="store_true",
        help="Skip port availability checks (recommended for CI runners).",
    )
    parser.add_argument(
        "--allow-env-from-process",
        action="store_true",
        help="Do not fail solely because .env/config.env is missing when env vars are injected by the process.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Optional path to write structured precheck results as JSON.",
    )
    return parser.parse_args(argv)


def _failure_levels(strict: bool, fail_on_warn: bool) -> set[str]:
    levels = {"BLOCKER"}
    if strict:
        levels.add("ACTION")
    if fail_on_warn:
        levels.add("WARN")
    return levels


def _write_json_report(path: Path, results: list[CheckResult], *, strict: bool, fail_on_warn: bool) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "fail_on_warn": fail_on_warn,
        "results": [{"level": item.level, "message": item.message} for item in results],
        "summary": {
            "checks_run": len(results),
            "blockers": sum(1 for item in results if item.level == "BLOCKER"),
            "actions": sum(1 for item in results if item.level == "ACTION"),
            "warnings": sum(1 for item in results if item.level == "WARN"),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("DataLogicEngine runtime precheck")
    print("===============================")

    results: list[CheckResult] = []
    for check in (
        check_python,
        check_node,
        check_backend_dependencies,
        check_templates_and_static,
    ):
        results.extend(check())
    results.extend(check_env_files(allow_env_from_process=args.allow_env_from_process))
    if args.skip_ports:
        print("\nPort availability")
        print("-----------------")
        print("[INFO] Port checks skipped via --skip-ports.")
        results.append(CheckResult("INFO", "Port checks skipped"))
    else:
        results.extend(check_ports())

    blockers = [r for r in results if r.level == "BLOCKER"]
    actions = [r for r in results if r.level == "ACTION"]
    warns = [r for r in results if r.level == "WARN"]
    failing_levels = _failure_levels(args.strict, args.fail_on_warn)
    failing_items = [r for r in results if r.level in failing_levels]

    print("\nSummary")
    print("-------")
    print(f"Checks run: {len(results)}")
    print(f"Blockers: {len(blockers)}")
    print(f"Action items: {len(actions)}")
    print(f"Warnings: {len(warns)}")
    print(f"Fail levels: {', '.join(sorted(failing_levels))}")

    if args.json_report:
        _write_json_report(args.json_report, results, strict=args.strict, fail_on_warn=args.fail_on_warn)
        print(f"JSON report written: {args.json_report}")

    if failing_items:
        print("\nPrecheck failed: resolve required findings above before starting the stack.")
        return 1

    print("\nPrecheck passed: required findings clear.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
