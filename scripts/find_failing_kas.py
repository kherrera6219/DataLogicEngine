import os
import subprocess
import json

def get_ka_files():
    ka_dir = os.path.join("backend", "knowledge_algorithms")
    files = [f for f in os.listdir(ka_dir) if f.startswith("ka_") and f.endswith(".py") and "master" not in f]
    return sorted(files)

ka_files = get_ka_files()
failed = []

for ka_file in ka_files:
    print(f"Testing {ka_file}...", end="\r")
    cmd = ["python", "-m", "pytest", f"backend/tests/test_ka_bulk.py::test_ka_contract[{ka_file}]", "--no-cov", "-q"]
    env = os.environ.copy()
    env["PYTHONPATH"] = ".;" + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"FAILED: {ka_file}")
        failed.append(ka_file)

print("\nFinal list of failing KAs:")
for f in failed:
    print(f)
