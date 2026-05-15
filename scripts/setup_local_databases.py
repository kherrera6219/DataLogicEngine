"""Download and extract portable database binaries for local QC mode.

Installs PostgreSQL 16, Redis, and Neo4j Community into the ``databases/``
directory that DatabaseLifecycleManager expects.  Safe to re-run — existing
installations are skipped.

Usage:
    python scripts/setup_local_databases.py [--pg] [--redis] [--neo4j] [--all]
    python scripts/setup_local_databases.py --all
    python scripts/setup_local_databases.py --verify
"""

import argparse
import os
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile

# ---------------------------------------------------------------------------
# Version pins
# ---------------------------------------------------------------------------

PG_VERSION = "16.2"
REDIS_VERSION = "5.0.14.1"
NEO4J_VERSION = "5.16.0"

# ---------------------------------------------------------------------------
# Download URLs
# ---------------------------------------------------------------------------

IS_WINDOWS = platform.system() == "Windows"

_PG_URL_WIN = (
    f"https://get.enterprisedb.com/postgresql/"
    f"postgresql-{PG_VERSION}-1-windows-x64-binaries.zip"
)
_REDIS_URL_WIN = (
    f"https://github.com/tporadowski/redis/releases/download/"
    f"v{REDIS_VERSION}/Redis-x64-{REDIS_VERSION}.zip"
)
# tporadowski/redis is a Windows port; latest release is 5.0.14.1
# If this 404s, download manually from https://github.com/tporadowski/redis/releases
_NEO4J_URL = (
    f"https://dist.neo4j.org/neo4j-community-{NEO4J_VERSION}-windows.zip"
    if IS_WINDOWS
    else f"https://dist.neo4j.org/neo4j-community-{NEO4J_VERSION}-unix.tar.gz"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASES_DIR = os.path.join(REPO_ROOT, "databases")


def _progress(block_num: int, block_size: int, total: int) -> None:
    downloaded = block_num * block_size
    if total > 0:
        pct = min(100, downloaded * 100 // total)
        bar = "#" * (pct // 2) + "." * (50 - pct // 2)
        mb = downloaded / 1_048_576
        total_mb = total / 1_048_576
        print(f"\r  [{bar}] {pct:3d}%  {mb:.1f}/{total_mb:.1f} MB", end="", flush=True)
    else:
        mb = downloaded / 1_048_576
        print(f"\r  Downloaded {mb:.1f} MB...", end="", flush=True)


def _download(url: str, dest: str) -> None:
    print(f"  Downloading from {url}")
    try:
        urllib.request.urlretrieve(url, dest, _progress)
        print()  # newline after progress bar
    except Exception as exc:
        print(f"\n  ERROR: Download failed - {exc}")
        raise


def _extract_zip(zip_path: str, dest_dir: str) -> None:
    print(f"  Extracting to {dest_dir} ...")
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)


def _flatten_single_subdir(parent: str) -> None:
    """If parent contains exactly one subdirectory, move its contents up."""
    entries = os.listdir(parent)
    if len(entries) == 1 and os.path.isdir(os.path.join(parent, entries[0])):
        subdir = os.path.join(parent, entries[0])
        for item in os.listdir(subdir):
            shutil.move(os.path.join(subdir, item), parent)
        os.rmdir(subdir)


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------

def setup_postgresql() -> bool:
    pg_dir = os.path.join(DATABASES_DIR, "postgresql")
    bin_name = "postgres.exe" if IS_WINDOWS else "postgres"
    pg_bin = os.path.join(pg_dir, "bin", bin_name)

    if os.path.exists(pg_bin):
        print(f"[PostgreSQL] Already installed at {pg_dir}")
        return True

    if not IS_WINDOWS:
        print("[PostgreSQL] Automatic install only supported on Windows.")
        print(f"  Install PostgreSQL 16 and set up bin/ at: {pg_dir}/bin/")
        return False

    print(f"[PostgreSQL {PG_VERSION}] Installing ...")
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "postgresql.zip")
        try:
            _download(_PG_URL_WIN, zip_path)
        except Exception:
            print("  Manual download:", _PG_URL_WIN)
            print(f"  Extract to: {pg_dir}/")
            return False

        _extract_zip(zip_path, pg_dir)
        _flatten_single_subdir(pg_dir)  # removes the pgsql/ wrapper

    os.makedirs(os.path.join(pg_dir, "data"), exist_ok=True)
    print(f"[PostgreSQL] Done - binary: {pg_bin}")
    return True


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------

def setup_redis() -> bool:
    redis_dir = os.path.join(DATABASES_DIR, "redis")
    bin_name = "redis-server.exe" if IS_WINDOWS else "redis-server"
    redis_bin = os.path.join(redis_dir, bin_name)

    if os.path.exists(redis_bin):
        print(f"[Redis] Already installed at {redis_dir}")
        return True

    if not IS_WINDOWS:
        print("[Redis] Automatic install only supported on Windows.")
        print(f"  Install Redis and place redis-server at: {redis_dir}/redis-server")
        return False

    print(f"[Redis {REDIS_VERSION}] Installing ...")
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "redis.zip")
        try:
            _download(_REDIS_URL_WIN, zip_path)
        except Exception:
            print("  Manual download:", _REDIS_URL_WIN)
            print(f"  Extract to: {redis_dir}/")
            return False

        _extract_zip(zip_path, redis_dir)
        _flatten_single_subdir(redis_dir)

    os.makedirs(os.path.join(redis_dir, "data"), exist_ok=True)
    print(f"[Redis] Done - binary: {redis_bin}")
    return True


# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------

def setup_neo4j() -> bool:
    neo4j_dir = os.path.join(DATABASES_DIR, "neo4j")
    bin_name = "neo4j.bat" if IS_WINDOWS else "neo4j"
    neo4j_bin = os.path.join(neo4j_dir, "bin", bin_name)

    if os.path.exists(neo4j_bin):
        print(f"[Neo4j] Already installed at {neo4j_dir}")
        return True

    print(f"[Neo4j Community {NEO4J_VERSION}] Installing ...")
    with tempfile.TemporaryDirectory() as tmp:
        archive_name = "neo4j.zip" if IS_WINDOWS else "neo4j.tar.gz"
        archive_path = os.path.join(tmp, archive_name)
        try:
            _download(_NEO4J_URL, archive_path)
        except Exception:
            print("  Automatic download failed. Download manually:")
            print(f"    URL: {_NEO4J_URL}")
            print(f"  Extract so that bin/neo4j exists at: {neo4j_dir}/bin/")
            return False

        if IS_WINDOWS:
            _extract_zip(archive_path, neo4j_dir)
        else:
            import tarfile
            os.makedirs(neo4j_dir, exist_ok=True)
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(neo4j_dir)

        _flatten_single_subdir(neo4j_dir)  # removes neo4j-community-x.y.z/ wrapper

    os.makedirs(os.path.join(neo4j_dir, "data"), exist_ok=True)
    print(f"[Neo4j] Done - binary: {neo4j_bin}")
    print("  Default credentials: neo4j / neo4j  (change on first login)")
    return True


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify() -> None:
    """Check whether expected binaries exist and ports are reachable."""
    import socket

    checks = [
        ("PostgreSQL binary", os.path.join(DATABASES_DIR, "postgresql", "bin",
                                            "postgres.exe" if IS_WINDOWS else "postgres")),
        ("Redis binary",      os.path.join(DATABASES_DIR, "redis",
                                            "redis-server.exe" if IS_WINDOWS else "redis-server")),
        ("Neo4j binary",      os.path.join(DATABASES_DIR, "neo4j", "bin",
                                            "neo4j.bat" if IS_WINDOWS else "neo4j")),
    ]

    port_checks = [
        ("PostgreSQL", int(os.environ.get("POSTGRES_LOCAL_PORT", "5432"))),
        ("Redis",      int(os.environ.get("REDIS_LOCAL_PORT", "6379"))),
        ("Neo4j",      int(os.environ.get("NEO4J_LOCAL_PORT", "7687"))),
    ]

    print("\n--- Binary presence ---")
    for label, path in checks:
        status = "OK" if os.path.exists(path) else "MISSING"
        print(f"  {status:7s}  {label}: {path}")

    print("\n--- Service reachability ---")
    for label, port in port_checks:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            up = s.connect_ex(("127.0.0.1", port)) == 0
        status = "UP" if up else "DOWN"
        print(f"  {status:7s}  {label} :{port}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download portable database binaries for DataLogicEngine local mode"
    )
    parser.add_argument("--pg",     action="store_true", help="Install PostgreSQL")
    parser.add_argument("--redis",  action="store_true", help="Install Redis")
    parser.add_argument("--neo4j",  action="store_true", help="Install Neo4j")
    parser.add_argument("--all",    action="store_true", help="Install all three")
    parser.add_argument("--verify", action="store_true", help="Check installed binaries and service ports")
    args = parser.parse_args()

    if args.verify:
        verify()
        return

    do_pg    = args.pg    or args.all
    do_redis = args.redis or args.all
    do_neo4j = args.neo4j or args.all

    if not (do_pg or do_redis or do_neo4j):
        parser.print_help()
        sys.exit(0)

    os.makedirs(DATABASES_DIR, exist_ok=True)
    print(f"databases/ -> {DATABASES_DIR}\n")

    results = {}
    if do_pg:
        results["PostgreSQL"] = setup_postgresql()
    if do_redis:
        results["Redis"] = setup_redis()
    if do_neo4j:
        results["Neo4j"] = setup_neo4j()

    print("\n--- Summary ---")
    for name, ok in results.items():
        print(f"  {'OK' if ok else 'FAILED':7s}  {name}")

    print("""
Next steps:
  1. Start the app:   python app.py  (databases auto-start)
  2. Seed Neo4j:      python scripts/seed_neo4j.py
  3. Run migrations:  .venv/Scripts/flask db upgrade
  4. Verify:          python scripts/setup_local_databases.py --verify
""")


if __name__ == "__main__":
    main()
