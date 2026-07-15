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
import tomllib
import re
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
    sqlite_path = _sqlite_database_path(database_url)
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        results.append(CheckResult("OK", "SQLite in-memory database configured for disposable CI/test runtime."))
    elif sqlite_path and sqlite_path.exists():
        results.append(CheckResult("OK", f"SQLite database file present at {sqlite_path}"))
    else:
        if database_url and not database_url.startswith("sqlite"):
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
        missing_level = "BLOCKER" if (env_values.get("FLASK_ENV") or "").strip().lower() == "production" else "ACTION"
        results.append(
            CheckResult(
                missing_level,
                f"Missing recommended configuration values: {missing_display}. Populate them in .env for stable startup.",
            )
        )

    if not env_values.get("DATABASE_URL"):
        level = "BLOCKER" if (env_values.get("FLASK_ENV") or "").strip().lower() == "production" else "ACTION"
        results.append(
            CheckResult(
                level,
                "DATABASE_URL is not set. SQLite is development/test-only; production requires supervised PostgreSQL.",
            )
        )

    provider_keys = (
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
    )
    if not any(env_values.get(key) for key in provider_keys):
        results.append(
            CheckResult(
                "ACTION",
                "No LLM provider key detected. Set at least one provider key for chat/runtime features.",
            )
        )

    flask_env = (env_values.get("FLASK_ENV") or "").strip().lower()
    auto_create_schema = str(env_values.get("AUTO_CREATE_SCHEMA") or "").strip().lower() == "true"
    if flask_env == "production":
        results.append(
            CheckResult(
                "WARN",
                "FLASK_ENV=production detected. For local HTTP development, use FLASK_ENV=development.",
            )
        )
        if auto_create_schema:
            results.append(
                CheckResult(
                    "BLOCKER",
                    "AUTO_CREATE_SCHEMA=true is unsafe for production startup. Apply migrations explicitly before boot.",
                )
            )
        if database_url.startswith("sqlite"):
            results.append(
                CheckResult(
                    "BLOCKER",
                    f"Production environment is configured with SQLite ({database_url}). Supervised PostgreSQL is required.",
                )
            )
    elif auto_create_schema:
        results.append(
            CheckResult(
                "WARN",
                "AUTO_CREATE_SCHEMA=true enabled. Use this only for disposable local environments.",
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
    req_lock = ROOT / "requirements.lock"
    pyproject_file = ROOT / "pyproject.toml"

    if req_file.exists():
        results.append(CheckResult("OK", f"requirements.txt found at {req_file}"))
        if req_lock.exists():
            results.append(CheckResult("OK", f"Hash-locked release dependencies found at {req_lock}."))
            results.append(CheckResult("INFO", "Install release dependencies with `pip install --require-hashes -r requirements.lock`."))
        else:
            results.append(CheckResult("ERROR", "requirements.lock is missing; regenerate the release dependency lock."))
    elif pyproject_file.exists():
        results.append(CheckResult("ERROR", "requirements.txt is missing; pyproject.toml is metadata-only."))
    else:
        results.append(CheckResult("BLOCKER", "No dependency manifest found (requirements.txt or pyproject.toml)."))

    if pyproject_file.exists():
        pyproject_name = _read_pyproject_name(pyproject_file)
        if not pyproject_name:
            results.append(CheckResult("ERROR", "pyproject.toml is missing project.name metadata."))
        else:
            results.append(CheckResult("OK", f"Python workspace metadata present (project.name={pyproject_name})."))

    venv_dir = ROOT / ".venv"
    if venv_dir.exists():
        results.append(CheckResult("OK", "Virtual environment directory detected at .venv."))
    else:
        results.append(CheckResult("WARN", "No .venv folder detected; create one to isolate dependencies."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def _sqlite_database_path(database_url: str) -> Path | None:
    """Resolve the SQLite file path using Flask-SQLAlchemy relative-path semantics."""
    if not database_url:
        return ROOT / "instance" / "ukg_database.db"

    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        return None

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None

    raw_path = database_url[len(prefix):]
    if not raw_path:
        return None

    path = Path(raw_path)
    if path.is_absolute():
        return path

    return ROOT / "instance" / path


def _read_pyproject_name(path: Path) -> str | None:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    project = payload.get("project")
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    return str(name).strip() if name else None


def _read_uv_virtual_package_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    for block in text.split("[[package]]"):
        if 'source = { virtual = "." }' not in block:
            continue
        match = re.search(r'name = "([^"]+)"', block)
        if match:
            return match.group(1).strip()
    return None


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
