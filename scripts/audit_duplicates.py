"""
Deep duplicate / misplaced-file audit.
Scans backend/ and core/ to find:
  1. Same module name appearing in both trees
  2. Same class name defined in multiple files
  3. Same function name (top-level) in multiple files
  4. Files in backend/ that look like they belong in core/ (no Flask/DB imports)
  5. Files in core/ that look like they belong in backend/ (Flask/DB imports -> already caught by inversion scan)
Writes results to audit_duplicates.txt
"""
import os
import ast
from collections import defaultdict

ROOT = r"C:\software\DataLogicEngine"
BACKEND = os.path.join(ROOT, "backend")
CORE    = os.path.join(ROOT, "core")

def walk_py(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)

def rel(path):
    return path.replace(ROOT + os.sep, "").replace("\\", "/")

def parse_names(path):
    """Return (classes, functions, imports) defined at top-level in path."""
    try:
        src = open(path, errors="ignore").read()
        tree = ast.parse(src)
    except Exception:
        return [], [], []
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and isinstance(getattr(n, 'col_offset', 0), int) and n.col_offset == 0]
    funcs   = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.col_offset == 0]
    imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.append(n.module)
    return classes, funcs, imports

def is_flask_heavy(imports):
    flask_markers = {"flask","sqlalchemy","flask_sqlalchemy","flask_login",
                     "flask_limiter","flask_mail","extensions","app","db"}
    for imp in imports:
        for m in flask_markers:
            if m in imp.lower():
                return True
    return False

# ── collect all files ──────────────────────────────────────────────────────
backend_files = list(walk_py(BACKEND))
core_files    = list(walk_py(CORE))

# ── 1. Module name collisions ──────────────────────────────────────────────
be_modules = {os.path.basename(f): f for f in backend_files}
co_modules = {os.path.basename(f): f for f in core_files}
shared_names = set(be_modules) & set(co_modules)
# Remove __init__.py — always shared
shared_names.discard("__init__.py")

# ── 2 & 3. Class / function collisions across the two trees ───────────────
class_map = defaultdict(list)   # classname -> [file1, file2, ...]
func_map  = defaultdict(list)

all_files_data = {}
for f in backend_files + core_files:
    cls, fns, imps = parse_names(f)
    all_files_data[f] = (cls, fns, imps)
    for c in cls:
        class_map[c].append(rel(f))
    for fn in fns:
        if not fn.startswith("_"):
            func_map[fn].append(rel(f))

dup_classes = {k: v for k, v in class_map.items() if len(v) > 1}
dup_funcs   = {k: v for k, v in func_map.items()
               if len(v) > 1
               # only cross-tree dups (one in backend, one in core)
               and any("backend/" in p for p in v)
               and any("core/" in p for p in v)}

# ── 4. backend/ files with no Flask/DB markers (candidates for core/) ──────
misplaced_in_backend = []
for f in backend_files:
    _, _, imps = all_files_data[f]
    fname = rel(f)
    # Skip obvious backend-specific dirs
    skip_dirs = ["routes/", "api/", "api_gateway/", "auth/", "models/",
                 "middleware/", "webhook_server/", "desktop/", "observability/"]
    if any(s in fname for s in skip_dirs):
        continue
    if not is_flask_heavy(imps):
        misplaced_in_backend.append(fname)

# ── write report ────────────────────────────────────────────────────────────
report_lines = []
report_lines.append("=" * 80)
report_lines.append("DUPLICATE / MISPLACED FILE AUDIT")
report_lines.append("=" * 80)

report_lines.append("\n## 1. MODULE NAME COLLISIONS (same filename in backend/ AND core/)")
report_lines.append(f"   {len(shared_names)} collision(s)\n")
for name in sorted(shared_names):
    report_lines.append(f"  {name}")
    report_lines.append(f"    BACKEND: {rel(be_modules[name])}")
    report_lines.append(f"    CORE:    {rel(co_modules[name])}")

report_lines.append("\n## 2. CLASS NAME DUPLICATES (same class defined in both trees)")
report_lines.append(f"   {len(dup_classes)} duplicate class name(s)\n")
for cls, paths in sorted(dup_classes.items()):
    report_lines.append(f"  class {cls}")
    for p in paths:
        report_lines.append(f"    {p}")

report_lines.append("\n## 3. TOP-LEVEL FUNCTION DUPLICATES (cross-tree)")
report_lines.append(f"   {len(dup_funcs)} duplicate function name(s)\n")
for fn, paths in sorted(dup_funcs.items()):
    report_lines.append(f"  def {fn}()")
    for p in paths:
        report_lines.append(f"    {p}")

report_lines.append("\n## 4. BACKEND FILES WITH NO FLASK/DB MARKERS (candidate for core/)")
report_lines.append(f"   {len(misplaced_in_backend)} file(s)\n")
for f in sorted(misplaced_in_backend):
    report_lines.append(f"  {f}")

with open(os.path.join(ROOT, "audit_duplicates.txt"), "w") as fh:
    fh.write("\n".join(report_lines))
print("Done. Results in audit_duplicates.txt")
print(f"Module collisions: {len(shared_names)}")
print(f"Class duplicates:  {len(dup_classes)}")
print(f"Function dups:     {len(dup_funcs)}")
print(f"Misplaced backend: {len(misplaced_in_backend)}")
