import sys
import subprocess
import time

PHASES = [
    {
        "name": "Phase 1: Unit & Core Logic",
        "targets": ["tests/unit", "tests/knowledge_algorithms", "tests/quad_persona", "tests/truth_engine", "tests/axes"]
    },
    {
        "name": "Phase 2: Integration & Routes",
        "targets": ["tests/integration", "tests/integration_routes", "tests/contract"]
    },
    {
        "name": "Phase 3: Security & Compliance",
        "targets": ["tests/security", "tests/compliance"]
    },
    {
        "name": "Phase 4: System & E2E",
        "targets": ["tests/end_to_end", "tests/simulation", "tests/resilience", "tests/windows", "tests/performance"]
    }
]

def run_phase(phase):
    print(f"\n{'='*50}")
    print(f"Running {phase['name']}...")
    print(f"{'='*50}")
    
    cmd = [sys.executable, "-m", "pytest"] + phase["targets"] + ["-v"]
    
    # We ignore coverage exit code 1 if it's just coverage. 
    # But pytest returns 1 for failures too.
    # To differentiate, we can check output or just be strict.
    # User said "zero error or warnings".
    # We'll pass `-W error` to treat warnings as errors if requested, but for now just running.
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n❌ {phase['name']} FAILED with exit code {result.returncode}")
        # Identify if it was just coverage failure (special code?) No, pytest-cov often uses 0 or 1.
        # But assuming normal pytest failure is 1.
        return False
        
    print(f"\n✅ {phase['name']} PASSED")
    return True

def main():
    print("Starting Phased Test Suite Execution...")
    start_time = time.time()
    
    for phase in PHASES:
        # Check if targets exist
        exists = [t for t in phase["targets"]] # Simplified check, subprocess will complain if not found but pytest handles directories.
        
        success = run_phase(phase)
        if not success:
            print("\n⛔ Execution STOPPED due to failure in previous phase.")
            sys.exit(1)
            
    duration = time.time() - start_time
    print(f"\n🎉 All phases completed successfully in {duration:.2f}s")

if __name__ == "__main__":
    main()
