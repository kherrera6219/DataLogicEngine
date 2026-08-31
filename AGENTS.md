# AGENTS.md — DataLogicEngine

Instructions for autonomous coding agents (Codex) working in this repository.
**Kevin Herrera is the sole maintainer and the only human reviewer.**

---

## 1. What this repo is

DataLogicEngine is **installed software**, not a SaaS product. It runs on a customer's workstation, server, or VM. Its approved boundary permits provider egress only to owner-configured model endpoints and exposes a local API to client software. CR-B must prove that enforcement; air-gapped operation is a target, not a currently verified capability. There is no approved license check-in, telemetry, or phone-home.

That deployment model is load-bearing for almost every decision here. **Do not add an outbound network call, a telemetry hook, an update check, or a crash reporter.** Any of those silently falsifies the product's central compliance claim. If a task seems to require one, stop and ask.

Current version 4.4.4, status `release_blocked`. Market: **United States only** — the product is not placed on the EU market, so EU CRA / EU AI Act / GDPR / NIS2 / DORA are out of scope.

---

## 2. Where the work is defined

An active remediation program governs most work in this repo. **Read these before starting any task.**

| Path | What it is |
|---|---|
| `docs/compliance/REMEDIATION_PLAN.md` | **The work orders.** 44 tasks (`CR-A0` … `CR-G12`) across 7 phases, each with a deterministic exit gate. Start here. |
| `docs/compliance/remediation_tasks.json` | Same tasks as structured data — dependencies, `allowed_paths`, gates, human-gate flags. Use this to pick the next unblocked task. |
| `docs/compliance/STANDARDS_BLUEPRINT.md` | Why each task exists — which standard or buyer requirement it serves. Read when a task's rationale is unclear. |
| `docs/compliance/EXTERNAL_REVIEW_2026-08-16.md` | The independent code review the findings came from. Read for the evidence behind a specific finding. |
| `reports/remediation/` | **Where you write generated evidence** — baselines, triage reports, inventories. Never edit files here by hand; they are produced by task steps. |
| `HANDOFF.md` | Human-facing narrative of project state. Long. Read the top section only unless directed further. |
| `docs/compliance/README.md` | Index of the above with reading order. |

**Picking work:** read `remediation_tasks.json`, find a task whose `depends_on` are all complete and whose `human_gate` is false, and execute it exactly as written in `REMEDIATION_PLAN.md`. Do not invent tasks.

**Phase A blocks the remediation phases.** The external review reported 40 Windows setup errors, but the 2026-08-20 4.4.1 repair run executed the full Windows suite with 3,295 passed, 18 skipped, and zero errors. CR-A0 must capture a fresh baseline before deciding whether CR-A1 still has work; do not treat the historical count as current or start Phases B–G before Phase A is formally dispositioned.

---

## 3. Hard rules — these override convenience

This codebase's characteristic failure mode is **silent degradation dressed up as intent**. It looks like this, and all three examples are real code from this repo:

```python
except Exception:
    return 0.5                    # failure and moderate confidence now indistinguishable

try:
    from backend.knowledge_algorithm.axis_mapper import AxisMapper   # inversion:ok
except Exception:
    self.axis_mapper = None       # permanently None; downstream silently no-ops

# inversion:ok                    # an inline claim of safety with no evidence behind it
```

Fixing a failing import by reaching for these patterns makes the error disappear and the defect permanent. **They are forbidden.**

1. **Never write a bare `except Exception` that returns a default value.** Failures propagate, or return an explicit typed error. A caller must always be able to tell "this failed" from "this succeeded with a low score."
2. **Never set an attribute to `None` on import failure.** Either the import succeeds or construction fails loudly.
3. **Never add a suppression** (`# inversion:ok`, `# type: ignore`, `# noqa`) without a same-line task-ID reference *and* a test proving the suppressed condition is safe.
4. **Never delete, skip, or weaken a test to make a gate pass.** A removed test is a removed control. If a test is genuinely wrong, stop and ask.
5. **Never document a capability as implemented that you have not executed.** A stale claim in a design document is what created this entire program.
6. **Never modify files outside the current task's `allowed_paths`.** If the fix requires it, stop and report — do not widen scope.
7. **No behavior changes in refactor tasks.** If a refactor requires changing business logic, stop and flag it.
8. **Verify a finding still exists before acting on it.** Findings were observed 2026-08-16 at commit `d24273ff`; the tree has moved. If the premise no longer holds, record that and close the task. Do not substitute adjacent work.

---

## 4. Commit and branch discipline

- One task = one commit, message prefixed with the task ID:
  `fix(test): [CR-A1] dispose engine in conftest teardown`
- One phase = one branch: `remediation/phase-a`, `remediation/phase-b`, …
- Never force-push. Never rebase a pushed branch.
- **If a gate fails three times, stop.** Revert to the last green commit and report. Do not keep trying variations.
- Leave the working tree clean at the end of every task. Evidence artifacts that reference commit state are worthless if the tree does not match the commit.

---

## 5. When to stop and ask Kevin

Stop — do not guess — on any of these:

- Anything marked `human_gate: true` in `remediation_tasks.json`
- Deleting, skipping, or retiring a test
- Changing an external-facing API schema or response contract
- Adding any new outbound network destination
- Adding a dependency
- Choosing a name for a renamed public field or metric
- Discovering a security defect not already recorded in the plan
- Any change that would alter the product's egress, air-gap, or data-handling claims

Report by writing the question into your task output. Do not open issues or send mail.

---

## 6. Test and quality commands

```bash
python -m pytest tests/ --no-cov -q --tb=short -rE    # full suite; -rE surfaces setup ERRORS
ruff check .                                          # lint; zero-warning policy
ruff format --check .
mypy backend/ sdk/
```

**Windows is the shipping platform.** A suite that is green on Linux and unexecuted on Windows is not green. Always confirm collection errors are zero, not just failures — pytest's exit code alone does not distinguish them.

---

## 7. First-run verification

The paths in §2 were authored outside the repo and have not been confirmed against this tree. **On your first task in this repo, verify them and correct this file if they are wrong:**

```bash
ls docs/compliance/ reports/remediation/ 2>&1
test -f docs/compliance/remediation_tasks.json && echo "tasks OK"
test -f HANDOFF.md && head -30 HANDOFF.md
```

If a path is missing, report it rather than creating files at a guessed location.

---

## 8. Scope note

Nested `AGENTS.override.md` files exist in some subdirectories and take precedence over this file when you are working there — see `tests/AGENTS.override.md`. Keep this file under 8 KiB; Codex caps combined AGENTS.md content at 32 KiB and silently stops loading once the limit is reached. **Add detail to the linked documents, not to this file.**
