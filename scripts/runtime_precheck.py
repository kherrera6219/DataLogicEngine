"""
Runtime environment precheck for the DataLogicEngine stack.

This script surfaces blocking issues that prevent the backend (Flask) and frontend (Next.js)
from starting and communicating locally. It focuses on developer default ports (backend 8080,
frontend 3000) and required configuration files.
"""
import os
import sys
import socket
import shutil
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

BACKEND_PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8080)))
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


def check_env_files() -> list[CheckResult]:
    header("Configuration files")
    results: list[CheckResult] = []
    env_files = [ROOT / ".env", ROOT / "config.env"]
    existing = [path for path in env_files if path.exists()]
    if not existing:
        results.append(CheckResult("BLOCKER", "Missing .env or config.env. Copy config.env to .env and adjust secrets."))
    else:
        for path in existing:
            results.append(CheckResult("OK", f"Found {path.name} at {path}"))

    sqlite_path = ROOT / "ukg_database.db"
    if sqlite_path.exists():
        results.append(CheckResult("OK", f"SQLite database file present at {sqlite_path}"))
    else:
        results.append(CheckResult("ACTION", "Initialize the database: `python -m flask db upgrade`"))

    env_values: dict[str, str | None] = {}
    for path in existing:
        env_values.update(dotenv_values(path))

    required_keys = ("SECRET_KEY", "DATABASE_URL")
    missing_keys = [key for key in required_keys if not env_values.get(key)]
    if missing_keys:
        missing_display = ", ".join(missing_keys)
        results.append(
            CheckResult(
                "ACTION",
                f"Missing recommended configuration values: {missing_display}. Populate them in .env for stable startup.",
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
        results.append(CheckResult("BLOCKER", "templates/ directory missing; Flask pages will fail to render."))

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
    if req_file.exists():
        results.append(CheckResult("OK", f"requirements.txt found at {req_file}"))
    else:
        results.append(CheckResult("BLOCKER", "requirements.txt missing; cannot install backend dependencies."))

    venv_site_packages = ROOT / "venv" / "lib"
    if venv_site_packages.exists():
        results.append(CheckResult("INFO", "Virtual environment directory detected; verify dependencies installed with `pip install -r requirements.txt`."))
    else:
        results.append(CheckResult("WARN", "No venv folder detected; create one to isolate dependencies."))

    for item in results:
        print(f"[{item.level}] {item.message}")
    return results


def main() -> int:
    print("DataLogicEngine runtime precheck")
    print("===============================")

    results: list[CheckResult] = []
    for check in (
        check_python,
        check_node,
        check_env_files,
        check_backend_dependencies,
        check_templates_and_static,
        check_ports,
    ):
        results.extend(check())

    blockers = [r for r in results if r.level == "BLOCKER"]
    actions = [r for r in results if r.level == "ACTION"]

    print("\nSummary")
    print("-------")
    print(f"Checks run: {len(results)}")
    print(f"Blockers: {len(blockers)}")
    print(f"Action items: {len(actions)}")

    if blockers:
        print("\nPrecheck failed: resolve blockers above before starting the stack.")
        return 1

    print("\nPrecheck passed: no blockers detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
