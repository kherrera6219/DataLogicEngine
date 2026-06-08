"""Find all route files anywhere in the repo outside of routes/"""
import os

ROOT = r"C:\software\DataLogicEngine"
SKIP = {"__pycache__", ".git", "node_modules", "htmlcov", ".venv", ".venv311"}

hits = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    rel_root = root.replace(ROOT + os.sep, "").replace("\\", "/")
    if rel_root.startswith("routes"):
        continue
    for f in files:
        if f.endswith("_routes.py") or f.endswith("_api.py") or "route" in f.lower():
            hits.append(rel_root + "/" + f)

with open(os.path.join(ROOT, "route_locations.txt"), "w") as fh:
    fh.write("\n".join(sorted(hits)))
print(f"Found {len(hits)} route-like files outside routes/")
for h in sorted(hits):
    print(" ", h)
