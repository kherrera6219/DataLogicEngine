"""
Replace the existing Complete Audit Plan in docs/audits/ with v2.0
and update TODO.md + HANDOFF.md to reference it.
"""
import os

ROOT = r"C:\software\DataLogicEngine"

V2_PATH = os.path.join(ROOT, r"docs\audits\DataLogicEngine_Complete_Audit_Plan_v2.md")

print(f"V2 plan written at: {V2_PATH}")
print("(Content written separately via Desktop Commander write_file)")

# ── 2. Patch TODO.md ──────────────────────────────────────────────────────────
todo_path = os.path.join(ROOT, "TODO.md")
todo = open(todo_path, encoding="utf-8").read()

todo = todo.replace(
    "**Last updated:** 2026-06-10 (complete audit plan session)",
    "**Last updated:** 2026-06-10 (complete audit plan v2.0 — all new items investigated)",
    1,
)

OLD_16 = (
    "16. [x] REPO-AUDIT-COMPLETE-PLAN: full remaining audit plan produced from live repo scan.\n"
    "    - Evidence: live MCP scan of all 1,049-commit repo on 2026-06-10. 32 audit areas\n"
    "      identified across ~36 sessions covering every unaudited folder: `backend/truth_engine/`,\n"
    "      `backend/dsqp/`, `backend/llm_gateway/`, `backend/local_model_acceleration/` (NEW — Sprint 6\n"
    "      Ollama/6-tier escalation, never audited), `backend/dmrf/`, `core/simulation/` (49 files),\n"
    "      all 117 KAs + config layer, `core/persona/quad/`, `backend/security/` (28 files),\n"
    "      `core/axes/` (duplicate axis number issue found), `backend/storage/`, `core/system/`,\n"
    "      `sdk/UKG_Python_SDK/`, full frontend, tests, and remaining backend subsystems.\n"
    "    - Four new discoveries not in any prior plan: (1) `backend/local_model_acceleration/` never\n"
    "      audited; (2) axes 14\u201317 each have duplicate Python files; (3) `core/self_evolving/\n"
    "      sekre_engine.py` unknown purpose/status; (4) `prompts/defense_supervisor.txt` at repo root\n"
    "      unknown what uses it.\n"
    "    - Audit file: `docs/audits/DataLogicEngine_Complete_Audit_Plan.md`\n"
    "    - Status: Plan complete. Phase 1 (live pipeline) is the immediate next execution priority.\n"
    "      Recommended first session: A4 `backend/local_model_acceleration/` (newest, unreviewed).\n"
)

NEW_16 = (
    "16. [x] REPO-AUDIT-COMPLETE-PLAN-V2: complete remaining audit plan v2.0 \u2014 all 4 new items"
    " investigated from live code reads + full conversation history review.\n"
    "    - N1 `core/self_evolving/sekre_engine.py`: SEKRE = Self-Evolving Knowledge Refinement"
    " Engine, 620 lines, fully implemented, **zero importers** \u2014 disconnected."
    " Wiring tasks defined: instantiate in system_initializer.py, call post-L10, add feedback endpoint.\n"
    "    - N2 `prompts/defense_supervisor.txt`: LLM injection/social-engineering/DAN detection prompt."
    " **Zero importers** \u2014 disconnected. Wire into prompt_injection_shield.py or ai_guardrail.py."
    " Add to PyInstaller datas.\n"
    "    - N3 Duplicate axis files: axis_system.py confirmed loading canonical set."
    " 4 legacy files (provenance, object_type, validation_state, security) never imported \u2014"
    " safe to delete. Delete tasks in Sprint 0.\n"
    "    - N4 Axis 4/5 gap: axis3_domain.py reused for Axis 4; Axis 5 has no dedicated manager."
    " Resolution tasks defined.\n"
    "    - Plan: `docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md`\n"
    "    - Scope: 32 audit areas, ~31 sessions, full Definition of Done (16 criteria).\n"
    "    - Sprint 0 starts immediately: RT-1, RT-2, RT-3, N3 (delete legacy axes), N4 (resolve gap).\n"
)

if OLD_16 in todo:
    todo = todo.replace(OLD_16, NEW_16, 1)
    print("Replaced item 16 in TODO.md with v2 reference")
else:
    print("WARNING: item 16 exact text not found; appending note")
    todo = todo.replace(
        "### Trace Viewer Wiring Phased Update Plan",
        NEW_16 + "\n### Trace Viewer Wiring Phased Update Plan",
        1,
    )

open(todo_path, "w", encoding="utf-8").write(todo)
print("TODO.md patched")

# ── 3. Patch HANDOFF.md ───────────────────────────────────────────────────────
handoff_path = os.path.join(ROOT, "HANDOFF.md")
handoff = open(handoff_path, encoding="utf-8").read()

handoff = handoff.replace(
    "_Last updated: 2026-06-10 (complete audit plan session)_",
    "_Last updated: 2026-06-10 (complete audit plan v2.0)_",
    1,
)

print("HANDOFF.md date updated" if "_Last updated: 2026-06-10 (complete audit plan v2.0)_" in handoff else "WARN: date not updated")

# Update plan filename reference
handoff = handoff.replace(
    "`docs/audits/DataLogicEngine_Complete_Audit_Plan.md`",
    "`docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md`",
)

open(handoff_path, "w", encoding="utf-8").write(handoff)
print("HANDOFF.md patched")
print("All done.")
