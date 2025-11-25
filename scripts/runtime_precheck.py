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
from pathlib import Path

BACKEND_PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8080)))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", 3000))
ROOT = Path(__file__).resolve().parents[1]


def header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def check_python() -> None:
    header("Python environment")
    major, minor = sys.version_info[:2]
    print(f"Detected Python: {major}.{minor}")
    if major < 3 or (major == 3 and minor < 11):
        print("[BLOCKER] Python 3.11+ required for parity with dependencies.")
    else:
        print("[OK] Python version meets minimum requirement (3.11+).")

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        print(f"[OK] Using virtualenv: {venv}")
    else:
        print("[WARN] Not running inside a virtual environment; recreate per README to avoid dependency conflicts.")


def check_node() -> None:
    header("Node.js environment")
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if not node_path:
        print("[BLOCKER] Node.js not found. Install Node 20.x to run the frontend.")
        return

    print(f"[OK] node found at {node_path}")
    if not npm_path:
        print("[BLOCKER] npm not found. Install Node.js with npm included.")
    else:
        print(f"[OK] npm found at {npm_path}")

    # Defer expensive version parsing; direct instructions are sufficient for now.
    frontend_dir = ROOT / "frontend" / "node_modules"
    if not frontend_dir.exists():
        print("[ACTION] Run `cd frontend && npm install` to install frontend dependencies.")
    else:
        print("[OK] Frontend dependencies directory detected.")


def check_env_files() -> None:
    header("Configuration files")
    env_files = [ROOT / ".env", ROOT / "config.env"]
    existing = [path for path in env_files if path.exists()]
    if not existing:
        print("[BLOCKER] Missing .env or config.env. Copy config.env to .env and adjust secrets.")
    else:
        for path in existing:
            print(f"[OK] Found {path.name} at {path}")

    sqlite_path = ROOT / "ukg_database.db"
    if sqlite_path.exists():
        print(f"[OK] SQLite database file present at {sqlite_path}")
    else:
        print("[ACTION] Initialize the database: `python -c \"from app import app, db; app.app_context().push(); db.create_all()\"`")


def check_ports() -> None:
    header("Port availability")
    for label, port in ("Backend", BACKEND_PORT), ("Frontend", FRONTEND_PORT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            if result == 0:
                print(f"[BLOCKER] {label} port {port} is already in use. Stop the process or choose a different port.")
            else:
                print(f"[OK] {label} port {port} is free.")


def check_templates_and_static() -> None:
    header("Backend templates & static assets")
    templates_dir = ROOT / "templates"
    static_dir = ROOT / "static"
    if templates_dir.exists():
        print(f"[OK] Templates directory located at {templates_dir}")
    else:
        print("[BLOCKER] templates/ directory missing; Flask pages will fail to render.")

    if static_dir.exists():
        print(f"[OK] Static assets directory located at {static_dir}")
    else:
        print("[WARN] static/ directory missing; some assets may not load.")


def check_backend_dependencies() -> None:
    header("Backend dependencies")
    req_file = ROOT / "requirements.txt"
    if req_file.exists():
        print(f"[OK] requirements.txt found at {req_file}")
    else:
        print("[BLOCKER] requirements.txt missing; cannot install backend dependencies.")

    venv_site_packages = ROOT / "venv" / "lib"
    if venv_site_packages.exists():
        print("[INFO] Virtual environment directory detected; verify dependencies installed with `pip install -r requirements.txt`.")
    else:
        print("[WARN] No venv folder detected; create one to isolate dependencies.")


def main() -> None:
    print("DataLogicEngine runtime precheck")
    print("===============================")
    check_python()
    check_node()
    check_env_files()
    check_backend_dependencies()
    check_templates_and_static()
    check_ports()


if __name__ == "__main__":
    main()
