# AGENTS.override.md — `tests/`

Overrides the root `AGENTS.md` while working anywhere under `tests/`.

---

## The rule that matters most here

**A test suite that reports "3068 passed" while 40 tests error at setup is not a passing suite.** Those 40 never ran. Always invoke with `-rE` and confirm the ERROR count is zero, not just the FAILED count:

```bash
python -m pytest tests/ --no-cov -q --tb=short -rE
```

Windows is the shipping platform. Linux-only green is not green.

---

## Historical setup-error premise to verify

The external review reported that `tests/conftest.py` unlinked a shared
repo-root SQLite file while an engine still held it open. The current
2026-08-20 Windows run no longer reproduces that outcome: 3,295 tests passed,
18 skipped, and zero setup errors occurred. CR-A0 must capture a fresh baseline,
and CR-A1 must rerun its premise-verification command before changing fixtures.
Do not implement the historical fix description unless the premise reproduces.

The casualties are concentrated in exactly the wrong place: anonymous-mutation denial across 18 endpoints, CSRF and origin enforcement, DPAPI secret boundaries, error-sentinel information disclosure, and GDPR data export.

**The fix is both halves, not one:**

1. `engine.dispose()` in fixture teardown, including on the exception path (`try/finally`, or teardown after the `yield`).
2. A unique database path per test under `tmp_path` / `tmp_path_factory`. The shared repo-root file is the root cause; disposing the engine alone treats the symptom and will regress.

**Explicitly forbidden as "fixes":**

- retry loops around `unlink()`
- `ignore_errors=True`
- `try/except PermissionError: pass`
- `os.remove` with a `sleep`

Each makes the error message disappear while leaving tests sharing state — which is worse than the original defect, because it is invisible.

---

## Rules for changing tests

- **Never delete, skip, `xfail`, or weaken a test to make a gate pass.** A removed test is a removed control. This is a stop-and-ask.
- A failing test is a finding until proven otherwise. Determine whether the **test** is wrong or the **code** is wrong, and write the determination down with evidence before changing either.
- If the code is wrong, fix the code in a **separate commit** from any test change, and note it explicitly in the task report.
- Adding a test is always allowed and never needs approval.
- New tests must assert behavior, not implementation. A test that passes because it mirrors the code's current structure catches nothing.

---

## Fixture hygiene going forward

- No shared mutable state at repo root — temp paths only.
- Every resource that can hold an OS handle (DB engines, file handles, sockets, subprocesses) gets explicit teardown.
- Prefer `tmp_path_factory` for session-scoped fixtures over any fixed path.
- Once `CR-A2` lands, `filterwarnings = ["error::pytest.PytestUnraisableExceptionWarning"]` is active — undisposed resources will fail the build rather than warn. That is intentional; do not relax it.

---

Task context: `CR-A1`, `CR-A2`, `CR-A3` in `docs/compliance/REMEDIATION_PLAN.md`.
