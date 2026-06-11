"""Remove the duplicate item 16 that got appended in the second patch run."""


path = r"C:\software\DataLogicEngine\TODO.md"
src = open(path, encoding="utf-8").read()

DUPE_MARKER = (
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
    "\n"
)

count = src.count(DUPE_MARKER)
print(f"Found {count} occurrences of the marker")

if count == 2:
    # Remove the second occurrence (the appended duplicate)
    first_pos = src.find(DUPE_MARKER)
    second_pos = src.find(DUPE_MARKER, first_pos + 1)
    src = src[:second_pos] + src[second_pos + len(DUPE_MARKER):]
    open(path, "w", encoding="utf-8").write(src)
    print("Removed duplicate item 16")
elif count == 1:
    print("Only one occurrence — no duplicate to remove")
else:
    print(f"Unexpected count: {count}")
