"""
Deep inspection of the high-priority duplicate classes/files.
Checks import counts, actual content similarity, and which version is 'live'.
"""
import os

ROOT = r"C:\software\DataLogicEngine"

def rel(p): return p.replace(ROOT + os.sep, "").replace("\\", "/")
def lines(p): return open(p, errors="ignore").readlines()
def src(p): return open(p, errors="ignore").read()

def count_importers(symbol, root_dirs=None):
    """Count how many files import a given module path or symbol."""
    if root_dirs is None:
        root_dirs = [os.path.join(ROOT, "backend"), os.path.join(ROOT, "core"),
                     os.path.join(ROOT, "routes"), os.path.join(ROOT, "tests")]
    count = 0
    files = []
    for d in root_dirs:
        if not os.path.exists(d):
            continue
        for r, dirs, fs in os.walk(d):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for f in fs:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(r, f)
                s = src(p)
                if symbol in s:
                    count += 1
                    files.append(rel(p))
    return count, files

out = []

# ─────────────────────────────────────────────────────────────────────────────
out.append("=" * 80)
out.append("DEEP DUPLICATE INSPECTION REPORT")
out.append("=" * 80)

# ── 1. simulation_engine.py ──────────────────────────────────────────────────
out.append("\n### A. simulation_engine.py  (3-way: backend/ + core/ + core/legacy)")
for path, label in [
    (r"backend\simulation\simulation_engine.py", "BACKEND"),
    (r"core\simulation\simulation_engine.py",    "CORE (runtime)"),
    (r"core\simulation\legacy_simulation_engine.py", "CORE (legacy)"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    short = os.path.basename(full).replace(".py", "")
    n, who = count_importers(short)
    out.append(f"  [{label}] {rel(full)}")
    out.append(f"    Lines: {len(ls)}  |  Importers: {n}")
    out.append(f"    Importers: {who[:5]}")

# ── 2. refinement_orchestrator.py ────────────────────────────────────────────
out.append("\n### B. RefinementOrchestrator  (3 definitions)")
for path, label in [
    (r"backend\truth_engine\truth_core\refinement_orchestrator.py", "BACKEND/truth_core"),
    (r"core\simulation\refinement_orchestrator.py",                  "CORE/simulation"),
    (r"core\system\refinement_orchestrator.py",                      "CORE/system"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers("refinement_orchestrator")
    out.append(f"  [{label}] {rel(full)}")
    out.append(f"    Lines: {len(ls)}  |  Importers: {n}")
    for i, line in enumerate(ls):
        if line.strip().startswith("class RefinementOrchestrator"):
            out.append(f"    Class at L{i+1}: {line.strip()[:80]}")
            break

# ── 3. quad_engine.py ────────────────────────────────────────────────────────
out.append("\n### C. QuadPersonaEngine / quad_engine.py  (2 definitions)")
for path, label in [
    (r"backend\quad_persona\quad_engine.py", "BACKEND/quad_persona"),
    (r"core\persona\quad\quad_engine.py",    "CORE/persona/quad"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers("quad_engine")
    out.append(f"  [{label}] {rel(full)}")
    out.append(f"    Lines: {len(ls)}  |  Importers: {n}")
    out.append(f"    Importers: {who[:8]}")

# ── 4. PersonaSufficiencyTool / GatewayPersonaSufficiencyTool ────────────────
# DUP-5 resolved (Sprint 5): backend copy deleted; both classes now live in
# core.persona.quad.persona_scaling.sufficiency.
out.append("\n### D. PersonaSufficiencyTool / GatewayPersonaSufficiencyTool  (consolidated — DUP-5 resolved)")
for path, label in [
    (r"core\persona\quad\persona_scaling\sufficiency.py", "CORE/persona/quad (canonical)"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers("persona_scaling.sufficiency")
    out.append(f"  [{label}] {rel(full)}")
    out.append(f"    Lines: {len(ls)}")
    out.append(f"    Importers: {who[:5]}")

# ── 5. location_context_engine.py ────────────────────────────────────────────
out.append("\n### E. LocationContextEngine  (2 definitions)")
for path, label in [
    (r"backend\location_context_engine.py",          "BACKEND root"),
    (r"core\simulation\location_context_engine.py",  "CORE/simulation"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers("location_context_engine")
    out.append(f"  [{label}] {rel(full)}")
    out.append(f"    Lines: {len(ls)}  |  Importers: {n}")
    out.append(f"    Importers: {who[:6]}")

# ── 6. integrity.py ──────────────────────────────────────────────────────────
out.append("\n### F. integrity.py  (backend = shim, core = real)")
for path, label in [
    (r"backend\security\integrity.py", "BACKEND/security (shim?)"),
    (r"core\security\integrity.py",    "CORE/security (canonical)"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers("from backend.security.integrity")
    n2, who2 = count_importers("from core.security.integrity")
    out.append(f"  [{label}] {rel(full)}  ({len(ls)} lines)")
    out.append(f"    Import via backend path: {n}  |  via core path: {n2}")
    out.append("    HEAD: " + repr("".join(ls[:5])))

# ── 7. AxisCoordinate / UnifiedCoordinateSystem ───────────────────────────────
out.append("\n### G. AxisCoordinate + UnifiedCoordinateSystem  (1 canonical coord system file)")
for path, label in [
    (r"core\coordinate_system.py",            "CORE root"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, who = count_importers(os.path.basename(path).replace(".py", ""))
    out.append(f"  [{label}] {rel(full)}  ({len(ls)} lines)  importers: {n}")
    out.append(f"    Importers: {who[:6]}")

# ── 8. AuditLogger ────────────────────────────────────────────────────────────
out.append("\n### H. AuditLogger  (2 definitions in backend/)")
for path, label in [
    (r"backend\security\audit_logger.py",          "BACKEND/security"),
    (r"backend\truth_engine\truth_memory\audit.py","BACKEND/truth_memory"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    n, _ = count_importers("audit_logger")
    out.append(f"  [{label}] {rel(full)}  ({len(ls)} lines)")

# ── 9. KA-50 collision ────────────────────────────────────────────────────────
out.append("\n### I. KA-050 collision (two files with same KA number)")
for path, label in [
    (r"backend\knowledge_algorithms\ka_117_knowledge_integrity_validator.py", "ka_117_knowledge_integrity_validator"),
    (r"backend\knowledge_algorithms\ka_50_summarization.py",                  "ka_50_summarization"),
]:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    ls = lines(full)
    out.append(f"  {rel(full)}  ({len(ls)} lines)")
    for i, line in enumerate(ls[:30]):
        if "class KA" in line or "class Ka" in line:
            out.append(f"    {line.strip()[:80]}")
            break

# ── 10. backend/core/ subdir ──────────────────────────────────────────────────
out.append("\n### J. backend/core/ subdirectory (suspicious — core logic inside backend/)")
bc = os.path.join(ROOT, r"backend\core")
if os.path.exists(bc):
    for f in os.listdir(bc):
        out.append(f"  backend/core/{f}")

with open(os.path.join(ROOT, "audit_deep.txt"), "w") as fh:
    fh.write("\n".join(out))
print("Done. Results in audit_deep.txt")
