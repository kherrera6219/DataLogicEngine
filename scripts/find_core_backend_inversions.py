"""Find all core -> backend import inversions."""
import os
from collections import defaultdict

results = []
for root, dirs, files in os.walk("core"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f).replace("\\", "/")
        for line_no, line in enumerate(open(os.path.join(root, f), errors="ignore"), 1):
            s = line.strip()
            if ("from backend" in s or "import backend" in s) and not s.startswith("#"):
                results.append((path, line_no, s))

by_file = defaultdict(list)
for p, line_no, s in results:
    by_file[p].append((line_no, s))

out = []
for p, items in sorted(by_file.items()):
    out.append(f"{p}  ({len(items)} inversion{'s' if len(items)>1 else ''})")
    for line_no, s in items:
        out.append(f"  L{line_no}: {s[:110]}")

out.append("")
out.append(f"TOTAL: {len(results)} import lines across {len(by_file)} files")

with open("core_backend_inversions.txt", "w") as fh:
    fh.write("\n".join(out))

print("\n".join(out))
