import subprocess
import sys
import time

PHASES = [
    {
        "name": "Phase 1: Unit & Core Logic",
        "targets": ["tests/unit", "tests/knowledge_algorithms", "tests/quad_persona", "tests/truth_engine", "tests/axes"]
    },
    {
        "name": "Phase 2: Integration & Routes",
        "targets": ["tests/integration", "tests/integration_routes", "tests/contract", "tests/parity"]
    },
    {
        "name": "Phase 3: Security & Compliance",
        "targets": ["tests/security", "tests/compliance"]
    },
    {
        "name": "Phase 4: System & E2E",
        # tests/resilience was removed; do not re-add without a real package.
        "targets": ["tests/end_to_end", "tests/simulation", "tests/windows", "tests/performance"]
    }
]


def run_phase(phase):
    print(f"\n{'=' * 50}")
    print(f"Running {phase['name']}...")
    print(f"{'=' * 50}")

    # Run phases without global pytest addopts so we can validate functional
    # pass/fail first; coverage gating happens once at the end on the full suite.
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *phase["targets"],
        "--override-ini",
        "addopts=",
        "-v",
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n[FAIL] {phase['name']} failed with exit code {result.returncode}")
        return False

    print(f"\n[PASS] {phase['name']}")
    return True


def run_full_coverage_gate():
    print(f"\n{'=' * 50}")
    print("Running full-suite coverage gate...")
    print(f"{'=' * 50}")

    cmd = [sys.executable, "-m", "pytest", "tests"]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(
            f"\n[FAIL] Coverage/full-suite validation failed with exit code "
            f"{result.returncode}"
        )
        return False

    print("\n[PASS] Coverage gate met on full suite")
    return True


def main():
    print("Starting Phased Test Suite Execution...")
    start_time = time.time()

    for phase in PHASES:
        success = run_phase(phase)
        if not success:
            print("\n[STOP] Execution stopped due to phase failure.")
            sys.exit(1)

    if not run_full_coverage_gate():
        print("\n[STOP] Execution stopped due to coverage/full-suite failure.")
        sys.exit(1)

    duration = time.time() - start_time
    print(f"\n[PASS] All phases and coverage gate completed in {duration:.2f}s")


if __name__ == "__main__":
    main()
