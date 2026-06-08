"""Patch TODO.md: update Last updated date, add audit entries to Next Work Queue."""
path = r"C:\software\DataLogicEngine\TODO.md"
src = open(path, encoding="utf-8").read()

# 1. Update the Last updated date
src = src.replace(
    "**Last updated:** 2026-06-07",
    "**Last updated:** 2026-06-07 (routes audit session)"
)

# 2. Add two new audit entries right before "### Trace Viewer Wiring Phased Update Plan"
INJECT_BEFORE = "### Trace Viewer Wiring Phased Update Plan"
NEW_ENTRIES = """14. [x] REPO-AUDIT-DUPS: duplicate class/file audit and sprint plan produced.
    - Evidence: `scripts/audit_duplicates.py` and `scripts/audit_deep.py` scanned live code and found 8 module name collisions, 17 duplicate class names, 2 cross-tree factory function duplicates, and 2 misplaced files in `backend/core/`. Full findings in `docs/audits/DataLogicEngine_Audit_Sprint_Plan_v2.md`. Note: Audit Sprints 1–3 already completed the execution of most findings from this audit; see AUDIT-SPRINT-1 through AUDIT-SPRINT-3 above.
    - Audit file: `docs/audits/DataLogicEngine_Audit_Sprint_Plan_v2.md`
15. [x] REPO-AUDIT-ROUTES: full routes audit — `routes/` and `backend/routes/` (all 22 route files).
    - Evidence: live read of all 22 route files. 20 issues found including 2 functional bugs (RT-1: 4 duplicate function names in multimodal_routes causing wrong handler dispatch; RT-2: unauthenticated `/search/suggest`), 5 unregistered blueprints (settings, analytics, retention, gdpr, privacy — all endpoints unreachable), and 3 overlapping user-data deletion implementations.
    - Sprint tasks: RT-1 through RT-18 — see `docs/audits/DataLogicEngine_Routes_Audit.md` for full task list and exit gates.
    - Audit file: `docs/audits/DataLogicEngine_Routes_Audit.md`
    - Status: Audit complete, sprint execution pending.

"""

if INJECT_BEFORE in src:
    src = src.replace(INJECT_BEFORE, NEW_ENTRIES + INJECT_BEFORE, 1)
    print("Injected audit entries")
else:
    print("WARNING: injection anchor not found")

# 3. Add routes sprint to the structural audit update paragraph
OLD_STRUCT = "Structural audit update: 2026-06-07. Sprints 1, 2, and 3 are complete."
NEW_STRUCT = (
    "Structural audit update: 2026-06-07. Sprints 1, 2, and 3 are complete. "
    "Routes audit completed 2026-06-07: 22 route files reviewed across `routes/` "
    "and `backend/routes/`; 20 issues identified; RT-1 through RT-18 sprint tasks defined."
)
src = src.replace(OLD_STRUCT, NEW_STRUCT, 1)

open(path, "w", encoding="utf-8").write(src)
print("TODO.md patched successfully")
