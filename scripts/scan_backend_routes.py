"""Quick structural scan of all backend/routes/ files — endpoints, auth decorators, blueprint names."""
import os

ROOT = r"C:\software\DataLogicEngine\backend\routes"

results = []
for fname in sorted(os.listdir(ROOT)):
    if not fname.endswith(".py") or fname.startswith("_"):
        continue
    path = os.path.join(ROOT, fname)
    src = open(path, errors="ignore").read()
    lines = src.splitlines()

    bp_name = None
    for line in lines:
        if "Blueprint(" in line:
            bp_name = line.strip()
            break

    endpoints = []
    for i, line in enumerate(lines):
        if "@" in line and ".route(" in line:
            decorators = []
            j = i
            while j < len(lines) and not lines[j].strip().startswith("def "):
                decorators.append(lines[j].strip())
                j += 1
            func_name = lines[j].strip()[:60] if j < len(lines) else "?"
            auth = [
                d for d in decorators
                if "login_required" in d or "api_login" in d or "api_admin" in d
            ]
            endpoints.append({
                "route": line.strip(),
                "func": func_name,
                "auth": auth[0] if auth else "NONE — NO AUTH",
            })

    results.append({
        "file": fname,
        "lines": len(lines),
        "blueprint": bp_name or "NOT FOUND",
        "endpoints": endpoints,
    })

out = []
for r in results:
    out.append(f"\n{'=' * 70}")
    out.append(f"FILE: {r['file']}  ({r['lines']} lines)")
    out.append(f"BLUEPRINT: {r['blueprint']}")
    out.append(f"ENDPOINTS: {len(r['endpoints'])}")
    for ep in r["endpoints"]:
        out.append(f"  {ep['route']}")
        out.append(f"    func: {ep['func']}")
        out.append(f"    auth: {ep['auth']}")

out_path = r"C:\software\DataLogicEngine\backend_routes_scan.txt"
with open(out_path, "w") as fh:
    fh.write("\n".join(out))
print("Done")
