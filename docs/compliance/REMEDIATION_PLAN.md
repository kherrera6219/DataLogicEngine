# DataLogicEngine — Compliance Remediation Plan (Agent-Executed)

**Version:** 1.1 *(rev. — US-only market decision applied, 2026-08-18)*
**Date:** August 17, 2026
**Target:** `C:\software\DataLogicEngine` @ main, v4.4.4 (`release_blocked`)
**Executor:** Codex (autonomous coding agent), reviewed by Kevin Herrera
**Source findings:** `DataLogicEngine_External_Review_2026-08-16.md`, `UKG_Standards_Compliance_Blueprint_2026-08-17.md`
**Conventions:** extends `DataLogicEngine_Audit_Sprint_Plan_v2.md` (task IDs, exit gates, one-task-one-commit)
**Verification update:** the source review was refreshed at `fd24536d`, but the
2026-08-27 4.4.3 qualification subsequently completed 3,317 Windows tests with
19 skipped and zero failures or setup errors. CR-A0 must capture a new commit-bound baseline
before CR-A1 is treated as open work. Other findings retain their task-level
verify-first requirements; CR-E1 and CR-E4 were found already satisfied.

**Assumption stated in the open:** this program remains a separate gate to
unblocking v4.4.4. Phase 19 established substantial pipeline wiring evidence,
but CP19-M installed/provider/signing acceptance remains independently open.
The CR task IDs are namespaced to avoid collision with the release program.

---

## 0. How this plan is built for an agent rather than a person

A plan written for a human can say "clean up the simulation tree" and rely on judgment. A plan written for Codex cannot. Four properties are enforced throughout:

**Every task ends in a command, not an opinion.** Each exit gate is a shell command with a pass/fail exit code. The agent never decides whether its work is done; the gate decides. Where a gate cannot be fully automated, the task is explicitly marked `HUMAN-GATE` and the agent must stop.

**Every task is self-contained.** Each work order restates its own context, so it can run in a fresh agent session with no memory of prior tasks. Task IDs carry their dependencies explicitly.

**Every task declares its blast radius.** `ALLOWED PATHS` lists what may be modified. Anything outside is out of bounds; the agent must stop and report rather than widen scope. This is the single most important control in an agent plan — scope creep is the dominant failure mode.

**Discovery precedes modification.** The findings below were observed on August 16, 2026 against commit `d24273ff`. The tree has 91 uncommitted changes and will have moved. Every task therefore begins with a verification step that confirms the finding still exists before acting on it. **If a task's premise no longer holds, the agent records that and closes the task — it does not invent adjacent work.**

### 0.1 The anti-patterns this codebase already has, which the agent must not reproduce

This matters more than any individual task. The repository's characteristic failure mode is **silent degradation dressed up as intent**, and it appears in at least three forms:

```python
except Exception:
    return 0.5                    # a failure and a moderate-confidence answer are now indistinguishable

try:
    from backend.knowledge_algorithm.axis_mapper import AxisMapper   # inversion:ok
except Exception as e:
    self.axis_mapper = None       # permanently None; downstream silently no-ops

# inversion:ok                    # an inline assertion of safety with no evidence behind it
```

An LLM fixing a failing import will reach for exactly these patterns, because they make the error go away. **They are forbidden in this plan.**

Hard rules for every task:

1. **Never add a bare `except Exception` that returns a default value.** If a subsystem fails, the failure propagates or is returned as an explicit error object. A caller must always be able to distinguish "this failed" from "this succeeded with a low score."
2. **Never add a `# inversion:ok`, `# type: ignore`, `# noqa`, or equivalent suppression** without a same-line reference to a task ID in this plan and a test that proves the suppressed condition is safe.
3. **Never set an attribute to `None` on import failure.** Either the import succeeds, or construction fails loudly.
4. **Never mark documentation as describing an implemented capability that you have not executed.** The gap between `UKG_Enterprise_Standards_Assessment.docx` and reality is the root cause of this entire plan.
5. **Never delete or weaken a test to make a gate pass.** If a test is wrong, that is a `HUMAN-GATE`.
6. **No behavior changes in refactor tasks.** If a fix requires changing business logic, stop and flag it.

### 0.2 Commit and branch discipline

- One task = one commit = one conventional-commit message prefixed with the task ID: `fix(test): [CR-A1] dispose engine in conftest teardown`
- One phase = one branch: `remediation/phase-a`, `remediation/phase-b`, …
- Never force-push. Never rebase a branch that has been pushed.
- If a gate fails after three attempts, stop, revert the working tree to the last green commit, and report. Do not keep trying variations.

### 0.3 Sizing

Estimates are in **agent sessions** (one focused Codex run ending at a gate), not human hours. Wall-clock is dominated by Kevin's review between tasks, not by generation.

---

## 1. Phase ordering and why it is not negotiable

```
Phase A  Trustworthy test harness      ← BLOCKS EVERYTHING
   │
   ├──▶ Phase B  Egress proof              (highest product value)
   ├──▶ Phase C  Local API hardening       (depends on A2 Windows CI)
   ├──▶ Phase D  Truth in claims           (independent of B/C)
   │
   └──▶ Phase E  Supply chain              (depends on A only)
            │
            └──▶ Phase F  Measurement       (depends on A; benefits from D1)
                     │
                     └──▶ Phase G  Documentation artifacts (depends on B, C, D, E, F)
```

**Phase A blocks the remediation phases and this is the whole point.** The review baseline reported forty Windows setup errors. The 2026-08-27 4.4.3 qualification later completed 3,317 Windows tests with 19 skipped and zero failures or setup errors, so the historical count is not a current finding. CR-A0 must capture a fresh commit-bound baseline and CR-A1 must reproduce its premise before modifying fixtures. Running Phases B–G before Phase A is formally dispositioned would still produce evidence without the program's approved baseline.

Phases B, C, D, and E are mutually independent once A is green and may be run concurrently in separate worktrees. Phase G is last because it documents what the others built; writing it earlier guarantees it documents intent rather than fact.

**Three exceptions may run in parallel with Phase A.** CR-D6 (retire or re-header the January assessment), CR-G1 (CVD policy + `security.txt`), and CR-G12 (Section 508 conformance report) touch no code and gate on no test.

**Decision HD-3 is resolved: the product is not being placed on the EU market.** That closes CR-G2 in its original form — there is no EU Cyber Resilience Act obligation, no September 11 reporting date, and no ENISA/CSIRT notification duty. CR-G2 is **replaced** by a US incident reporting runbook (DFARS 252.204-7012, CIRCIA when final, and customer contractual windows), and CR-G1 drops from urgent to routine — a published CVD process is still expected in federal procurement and still costs two pages.

**The consequence worth stating explicitly: this program now has no external deadline.** Every task below is justified by a buyer asking a question, not by a regulator setting a date. That is a weaker forcing function and a better reason — sequence by which deal you are chasing.

---

## PHASE A — Make the test harness trustworthy

**Blocks:** every other phase.
**Branch:** `remediation/phase-a`
**Sessions:** 3–5

### CR-A0 · Capture the verified baseline

**Depends on:** nothing
**Allowed paths:** `reports/remediation/` (new files only)

Nothing in this plan can be measured against an unknown starting point, and the tree has 91 uncommitted changes as of the review.

**Steps**

1. Report the working tree state — `git status --porcelain` and `git rev-parse HEAD`. **Do not commit or discard uncommitted changes.** Record them and stop for Kevin if the diff is non-trivial (`HUMAN-GATE`).
2. Run the full suite on Windows and capture verbatim output:
   `python -m pytest tests/ --no-cov -q --tb=no -rEf > reports/remediation/baseline_pytest.txt 2>&1`
3. Record the summary line, and separately enumerate every test that reports `ERROR` (setup failures) versus `FAILED`.
4. Capture `ruff check . --statistics`, `mypy backend/ sdk/ 2>&1 | tail -5`, and the first-party line counts.
5. Write `reports/remediation/BASELINE.md` with all of the above plus the commit SHA and timestamp.

**Exit gate**

```bash
test -f reports/remediation/BASELINE.md && \
test -f reports/remediation/baseline_pytest.txt && \
grep -qE "(error|passed)" reports/remediation/baseline_pytest.txt
```

**Non-goals:** fixing anything. This task only observes.

---

### CR-A1 · Fix the conftest database lock (the highest-value single change in this plan)

**Depends on:** CR-A0
**Allowed paths:** `tests/conftest.py`, `tests/**/conftest.py`
**Sessions:** 1

**Finding to verify first.** The review reported at `tests/conftest.py:150` that the fixture called `TEST_DB_PATH.unlink()` on a shared repo-root file `test_suite.sqlite3` while an engine remained open, producing `PermissionError: [WinError 32]`. The current full Windows run does not reproduce that result. Run the premise check before changing anything; if it remains absent, record and close the task rather than applying the historical proposed fix.

Confirm the mechanism before changing anything:

```bash
python -m pytest tests/ --no-cov -q --tb=line 2>&1 | grep -c "WinError 32"
```

**Required fix — both halves, not one**

1. **Dispose the engine in fixture teardown.** Find every place a SQLAlchemy `Engine` or `Session` is created in test fixtures and ensure `engine.dispose()` runs in teardown, including on the exception path (`try/finally` or a yield-fixture with teardown after the yield).
2. **Give each test a unique database path.** Replace the shared repo-root `test_suite.sqlite3` with a per-test path under pytest's `tmp_path`/`tmp_path_factory`. A shared file at the repo root is the root cause; disposing the engine alone treats the symptom and will regress.

**Explicitly forbidden:** retry loops around `unlink()`; `ignore_errors=True`; wrapping the unlink in `try/except PermissionError: pass`; `os.remove` with a sleep. Each of these makes the error message disappear while leaving tests sharing state.

**Exit gate**

```bash
python -m pytest tests/ --no-cov -q --tb=short -rE 2>&1 | tee reports/remediation/a1_pytest.txt
# Gate: zero lines matching "^ERROR" and zero "WinError 32"
! grep -qE "^ERROR" reports/remediation/a1_pytest.txt && \
! grep -q "WinError 32" reports/remediation/a1_pytest.txt
```

Collected-test count must be greater than or equal to the CR-A0 baseline (3,126 as reviewed). A gate that passes by collecting fewer tests is a failed gate.

---

### CR-A2 · Windows CI that fails the build on errors

**Depends on:** CR-A1
**Allowed paths:** `.github/workflows/`, `pyproject.toml` (pytest config only)
**Sessions:** 1

The security suite is green on the platform you do not ship to and unexecuted on the one you do. Fix the asymmetry structurally so it cannot recur.

**Steps**

1. Add a workflow running the full suite on `windows-latest` against the supported Python versions.
2. **The job must fail on collection errors, not only on test failures.** Add `-rEf` and assert on the summary; do not rely on pytest's exit code alone to distinguish the two.
3. Add `--strict-markers` and `filterwarnings = ["error::pytest.PytestUnraisableExceptionWarning"]` so undisposed resources surface as failures rather than warnings — this is what makes CR-A1 permanent.
4. Keep the Linux job. The point is parity, not replacement.
5. Add a required-status-check note to `docs/` for Kevin to enable in branch protection (`HUMAN-GATE` — repository settings are not the agent's to change).

**Exit gate**

```bash
python -c "import yaml,glob,sys; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]" && \
grep -rq "windows-latest" .github/workflows/ && \
grep -rq -- "-rE" .github/workflows/
```

---

### CR-A3 · Triage and green the 40 previously-unexecuted tests

**Depends on:** CR-A1, CR-A2
**Allowed paths:** `tests/`, plus any source file a genuine test failure proves is broken — **but source changes require a separate commit and an explicit note in the task report**
**Sessions:** 1–2

The review baseline said these 40 tests had not run on Windows. They were part of the successful 2026-08-20 full Windows collection, but CR-A0/CR-A3 still require individual recorded dispositions against the new commit-bound baseline.

The affected files, per the review:

- `tests/security/test_phase1_anonymous_mutations.py` — anonymous mutation denial across 18 endpoints including `/api/v1/truth/gate/evaluate` and `/graphql`
- `tests/security/test_session_security.py` — CSRF enforcement, untrusted-origin blocking, desktop-auth precedence
- `tests/security/test_phase1_secret_boundaries.py` — `test_provider_credentials_use_dpapi_at_rest`
- `tests/security/test_phase1_public_error_sentinels.py` — error normalization / information disclosure
- `TestGDPRDataExport` — GDPR data export
- the `test_fuzz_ukg_knowledge` fuzz series

**Steps**

1. Run each file individually and record pass/fail.
2. For each failure, determine whether the **test** is wrong or the **code** is wrong. Write the determination down with the evidence.
3. Fix code defects. **Do not modify a test to make it pass** unless you can demonstrate the test asserts something incorrect — and that is a `HUMAN-GATE`.
4. Report the count of genuine security defects found. This number goes in `reports/remediation/A3_TRIAGE.md` and is the honest measure of what the Windows gap was hiding.

**Exit gate**

```bash
python -m pytest tests/security/test_phase1_anonymous_mutations.py \
  tests/security/test_session_security.py \
  tests/security/test_phase1_secret_boundaries.py \
  tests/security/test_phase1_public_error_sentinels.py --no-cov -q 2>&1 | tail -3
# Gate: all pass, zero errors, and reports/remediation/A3_TRIAGE.md exists
```

**PHASE A EXIT GATE.** Full suite green on Windows CI with zero collection errors; collected count ≥ baseline; `A3_TRIAGE.md` written. **No other phase begins until this is true.**

---

## PHASE B — Prove the egress claim

**Why this phase exists.** DataLogicEngine's compliance position rests on one assertion: the only outbound connection is to the configured model endpoint. That assertion currently lives in a README. Converting it into an enforced, tested, logged property is the highest-value engineering work available — it is simultaneously the answer to HIPAA risk analysis, NIST 800-53 SC-7 and AC-4 for a customer's ATO, EU AI Act Art. 12 logging, and GDPR Art. 30 records. One artifact, five frameworks.

**Depends on:** Phase A complete
**Branch:** `remediation/phase-b`
**Sessions:** 5–7

### CR-B0 · Map every outbound call site

**Allowed paths:** `reports/remediation/` (new files only)

Discovery only — no code changes.

Enumerate every place the process can open a network connection: direct `requests`/`httpx`/`aiohttp`/`urllib` calls, LLM provider SDKs (`openai`, `anthropic`, `google-generativeai`, Azure), MCP client transports, telemetry or update checks, package-manager or model-download calls at runtime, and anything in `scripts/` that runs in production.

Produce `reports/remediation/EGRESS_INVENTORY.md`: file, line, library, destination (literal or config-derived), and whether it executes on the governed request path.

**Exit gate:** `EGRESS_INVENTORY.md` exists and lists at least every module importing an HTTP client. Cross-check with:

```bash
grep -rEn "requests\.|httpx\.|aiohttp|urllib\.request|socket\.(create_connection|connect)" backend/ core/ sdk/ --include="*.py" | wc -l
```

The inventory's call-site count must be ≥ this number. **If any call site targets a destination other than a configured model endpoint or an MCP server, stop and report it as a finding** — it contradicts the product's central compliance claim and Kevin needs to know before anything is built on top of it.

---

### CR-B1 · Single egress chokepoint with a default-deny allowlist

**Depends on:** CR-B0
**Allowed paths:** new `core/security/egress_guard.py` (or the equivalent location established by CR-B0), plus the call sites the inventory identified
**Sessions:** 2

**Design requirements**

- One module through which all outbound HTTP must pass. Default deny. An empty allowlist means zero egress, not unrestricted egress — this inversion is a common and catastrophic default.
- Allowlist entries are host-based and configured explicitly. Wildcards are permitted only at the leftmost label and must be logged as such.
- A denied connection raises a typed, explicit exception. **It does not return `None`, an empty response, or a degraded result** (see §0.1).
- The guard is enforced at the lowest practical layer — a custom transport or session factory — so that a new call site added later is denied by default rather than silently permitted. If a developer can bypass the guard by importing `requests` directly, the guard is decorative. Add a lint rule or import hook that makes direct imports fail.
- Configuration is explicit and inspectable at runtime via an API endpoint or CLI command, so a customer's security team can read the effective allowlist without reading source.

**Non-goals:** proxy support, TLS interception, per-request policy engines. Keep it small enough to be obviously correct.

**Exit gate**

```bash
python -m pytest tests/security/test_egress_guard.py --no-cov -q && \
python -m pytest tests/ --no-cov -q 2>&1 | tail -2   # no regression
```

New tests must cover: allowed host succeeds; denied host raises the typed exception; empty allowlist denies everything; the exception is not swallowed anywhere on the governed path.

---

### CR-B2 · Route every call site through the guard

**Depends on:** CR-B1
**Allowed paths:** call sites from `EGRESS_INVENTORY.md`
**Sessions:** 1–2

Migrate each inventoried call site to the guarded transport. Include MCP client transports — **each MCP server is a second egress path, and an unguarded one silently falsifies the product's one-outbound-flow claim.**

**Exit gate**

```bash
# No direct HTTP client usage outside the guard module
! grep -rEn "^\s*(import requests|import httpx|from requests|from httpx|import aiohttp)" \
  backend/ core/ sdk/ --include="*.py" | grep -v "egress_guard.py"
python -m pytest tests/ --no-cov -q 2>&1 | tail -2
```

---

### CR-B3 · Egress events into the hash-chained audit log

**Depends on:** CR-B2
**Allowed paths:** `core/security/egress_guard.py`, `backend/security/audit_logger.py`
**Sessions:** 1

Every outbound attempt — allowed or denied — becomes an audit event: timestamp, destination host, byte count out, byte count in, allow/deny, and the correlation ID of the governed request that caused it. **Content is never logged**; this is the metadata record that lets a customer verify the egress claim without exposing what was sent.

This converts "trust us" into "verify us," which is the product's own thesis applied to itself.

**Exit gate**

```bash
python -m pytest tests/security/test_egress_audit.py --no-cov -q
```

Tests must prove: an allowed call produces exactly one audit event; a denied call produces exactly one audit event with `result=deny`; no prompt or response body appears in any audit record.

---

### CR-B4 · Air-gap mode

**Depends on:** CR-B1
**Allowed paths:** config module, `core/security/egress_guard.py`, docs
**Sessions:** 1

A single explicit setting that disables all egress and requires a locally-reachable model endpoint (Ollama, vLLM, LM Studio, or a customer-hosted OpenAI-compatible service). In this mode the product must be fully functional against a local model, and any code path that would require a remote call must fail with a clear, actionable error rather than degrade.

This is the strongest single compliance feature the product has: it removes the HIPAA Business Associate question, the EU transfer question, and the federal data-egress objection in one move.

**Exit gate**

```bash
python -m pytest tests/security/test_airgap_mode.py --no-cov -q
```

Tests must prove a full governed request completes end-to-end with air-gap enabled and a local mock model, with the guard's allowlist empty for all non-loopback hosts.

---

### CR-B5 · CI egress test — the renewable evidence artifact

**Depends on:** CR-B2, CR-B4
**Allowed paths:** `.github/workflows/`, `tests/security/`
**Sessions:** 1–2

This is the task that turns the egress claim into an artifact you can hand a customer's security team.

**Steps**

1. Add a CI job that runs the full governed execution path under network observation: a deny-all environment with a single logging proxy, or an equivalent socket-level recorder.
2. Assert that the set of contacted hosts is exactly the configured model endpoint — **no other host, including telemetry, analytics, package registries, crash reporters, or font/CDN fetches.**
3. Emit the observed host list as a dated build artifact (`reports/egress/egress-attestation-<sha>.json`). Dated, renewable, reproducible evidence is the strongest kind in any framework.
4. Fail the build on any unexpected host.

**Exit gate**

```bash
grep -rq "egress" .github/workflows/ && \
python -m pytest tests/security/test_egress_ci_harness.py --no-cov -q && \
test -f reports/egress/README.md
```

---

### CR-B6 · Publish the effective egress configuration

**Depends on:** CR-B3
**Allowed paths:** API layer, CLI, docs
**Sessions:** 1

Expose a read-only endpoint and CLI command that print the effective allowlist, air-gap state, and configured model endpoint. A customer's assessor must be able to verify the product's boundary claim on a running instance without reading source or trusting documentation.

**Exit gate:** endpoint returns the effective configuration; test asserts it reflects a runtime config change; no secrets (API keys, tokens) appear in the output.

**PHASE B EXIT GATE.** CI egress job green and producing a dated attestation artifact; air-gap mode proven end-to-end; egress events in the audit chain; zero unguarded HTTP clients in first-party code.

---

## PHASE C — Harden the local API

**Why this phase exists.** With no cloud service, the local API to the client software is the entire remotely-reachable attack surface. It runs with the user's privileges on a workstation, server, or VM. The tests that cover it are exactly the ones Phase A resurrected.

**Depends on:** Phase A complete
**Branch:** `remediation/phase-c`
**Sessions:** 3–4

### CR-C1 · Verify and enforce loopback-default binding

**Allowed paths:** server startup/config modules, docs
**Sessions:** 1

Determine the default bind address. If it is anything other than loopback, that is a finding and must be changed.

Requirements: loopback by default; binding to `0.0.0.0` or a routable interface requires an explicit configuration value, logs a prominent warning at startup, and is documented in the hardening guide with the controls an operator must add. This is the most common finding in on-prem software penetration tests and it is trivially preventable.

**Exit gate**

```bash
python -m pytest tests/security/test_bind_address.py --no-cov -q
```

Tests must prove: default config binds loopback only; the non-loopback path requires the explicit flag; the warning is emitted.

---

### CR-C2 · Authenticate every request, including from localhost

**Depends on:** CR-C1, CR-A3
**Allowed paths:** API middleware/auth modules
**Sessions:** 1–2

Localhost is not a trust boundary. On a multi-user server, a Citrix/RDS host, or a VM running other workloads, any local process can reach a loopback listener.

Verify — and fix if needed — that every endpoint requires authentication, that CSRF and origin checks are enforced on anything browser-reachable, that no endpoint permits anonymous mutation, and that errors are normalized so internal state does not leak.

The tests for all four already exist. Phase A made them run. This task closes whatever they now reveal.

**Exit gate**

```bash
python -m pytest tests/security/test_phase1_anonymous_mutations.py \
  tests/security/test_session_security.py \
  tests/security/test_phase1_public_error_sentinels.py --no-cov -q
```

---

### CR-C3 · Verify the audit chain on read, not just on write

**Depends on:** CR-A1
**Allowed paths:** `backend/security/audit_logger.py`, `backend/truth_engine/truth_memory/`
**Sessions:** 1

The SHA-512 hash chain is written. Confirm that production code **verifies** it when reading, and that verification failure surfaces as a loud, explicit error.

An unverified chain is a data structure, not a control — and it is the control that carries EU AI Act Art. 12, NIST 800-53 AU-9, HIPAA §164.312(b), and SEC 17a-4 WORM-equivalence simultaneously.

Add a verification API/CLI so a customer can validate their own log.

**Exit gate**

```bash
python -m pytest tests/security/test_audit_chain_verification.py --no-cov -q
```

Tests must prove: a valid chain verifies; a chain with an altered entry fails verification with a specific error naming the broken link; a chain with a removed entry fails; verification runs on the production read path.

---

### CR-C4 · Least-privilege runtime check

**Allowed paths:** startup checks, docs
**Sessions:** 1

Confirm the product does not require local administrator at runtime. Document the exact rights the service account needs. Add a startup check that warns when running with more privilege than required.

**Exit gate:** documented privilege requirements in planned output docs/DEPLOYMENT_HARDENING.md; startup check tested.

**PHASE C EXIT GATE.** All local-API security tests green on Windows CI; loopback default proven; audit chain verified on read.

---

## PHASE D — Make the claims true

**Why this phase exists.** As installed software, your documentation is a set of representations to a buyer rather than internal notes. Three claims currently outrun the code: a probabilistic confidence score that is not probabilistic, a "live pipeline engine" that is permanently disabled, and a manifest of 211 production-enabled capabilities against roughly 20 on the live path.

**Depends on:** Phase A complete
**Branch:** `remediation/phase-d`
**Sessions:** 4–6

### CR-D1 · Rename the confidence score and stop swallowing exceptions · `HUMAN-GATE` on the name

**Allowed paths:** `backend/truth_engine/confidence_calculator.py` and every referencing site
**Sessions:** 1–2

**The finding.** 147 lines computing `C = 0.35·evidence_quality + 0.30·ka_consensus + 0.20·persona_agreement + 0.15·gate_factor`, where each component is a heuristic ratio. Missing evidence returns `0.5`. Missing KA data returns `0.5`. Missing personas returns `0.5`. A missing gate decision returns `0.8`. The whole `calculate()` body is wrapped in `except Exception: return 0.5`. Meanwhile `0.995` is hard-wired as the healthcare/finance/legal/safety threshold across `trust_validation_gateway.py`, `opa_policy.py`, and roughly a dozen other sites.

A run in which four subsystems silently failed produces a number indistinguishable from a run that genuinely reached moderate confidence.

**Two changes, both required**

1. **Rename.** The current name asserts a probability the quantity does not carry. `governance_score` or `check_pass_ratio` are both honest. **Kevin picks the name — the agent stops here on the first run and proceeds once the name is supplied.** Update the docstring to describe what is actually computed and remove the citation to "spec Section 13," which describes a different formula (`C = σ(α·Σ(wᵢ·eᵢ) − β·conflicts − γ·H)` — sigmoid, conflict penalty, entropy term, none of which are implemented).
2. **Make failures visible.** Remove every default-on-failure return. A missing component yields an explicit, typed incomplete result naming which inputs were unavailable. Remove the blanket `except Exception`. Callers must be able to distinguish failure from moderate confidence.

**Explicitly forbidden:** implementing the sigmoid formula in this task. Changing the math before there is any way to measure whether the change is an improvement swaps one unvalidated number for another. That is Phase F's job, and only after F2 exists.

**Exit gate**

```bash
! grep -rn "except Exception" backend/truth_engine/confidence_calculator.py && \
! grep -rn "return 0\.5\|return 0\.8" backend/truth_engine/confidence_calculator.py && \
python -m pytest tests/ --no-cov -q 2>&1 | tail -2
```

---

### CR-D2 · Propagate the rename across all threshold sites

**Depends on:** CR-D1
**Allowed paths:** all referencing files, `docs/`
**Sessions:** 1

Update every consumer, including `trust_validation_gateway.py`, `opa_policy.py`, policy files, API response schemas, and documentation. Any external-facing schema change is a breaking API change and belongs in the changelog and the SDK version bump.

**Exit gate**

```bash
! grep -rn "confidence.*0\.995" --include="*.py" --include="*.yaml" --include="*.md" . | grep -v CHANGELOG && \
python -m pytest tests/ --no-cov -q 2>&1 | tail -2
```

---

### CR-D3 · Archive `core/simulation/`

**Depends on:** CR-A1
**Allowed paths:** `core/simulation/`, `archive/`, the three importing test files
**Sessions:** 1–2

**The finding.** `core/simulation/simulation_engine.py` is 1,444 lines described in the June audit as "the live pipeline engine." Its constructor imports `backend.knowledge_algorithm` — **singular** — a package that does not exist (only `backend.knowledge_algorithms`, plural, 227 files). The imports always fail, the `except` always fires, and `axis_mapper`, `truth_engine`, and `workflow_loader` are always `None`. Consequently line 629 makes workflow step loading a permanent no-op and line 1341 means the 17-axis vector is never computed in this engine. `core/simulation/refinement_workflow.py` has the same defect at lines 31–35.

Three active test files still import it: `test_phase19_cp19b_contract_parity.py`, `test_sekre_wiring.py`, `test_phase10_simulation_authority.py`.

**Verify first:**

```bash
python -c "import backend.knowledge_algorithm" ; echo "exit=$?"   # expect ModuleNotFoundError
python -c "import backend.knowledge_algorithms; print('ok')"
```

**Steps**

1. Confirm Phase 19's position that `GovernedExecutionOrchestrator` is the only product path.
2. Move `core/simulation/` to `archive/core_simulation/` with a `README.md` stating the date, the reason, and the commit it was live at.
3. Delete the dead import blocks rather than carrying them into the archive.
4. Repoint or retire the three test files. If a test genuinely covers current behavior, it must be repointed at the governed path; if it only covers the dead engine, retire it with a note. **Retiring a test is a `HUMAN-GATE`.**
5. Note the near-collision between `knowledge_algorithm` and `knowledge_algorithms` — two package names one character apart, one of which no longer exists — in the developer guide.

**Exit gate**

```bash
test ! -d core/simulation && test -d archive/core_simulation && \
! grep -rn "backend\.knowledge_algorithm\b" --include="*.py" . && \
python -m pytest tests/ --no-cov -q 2>&1 | tail -2
```

---

### CR-D4 · Audit every suppression comment

**Depends on:** CR-D3
**Allowed paths:** the 8 files carrying suppressions, `reports/remediation/`
**Sessions:** 1

Nineteen `# inversion:ok` suppressions across 8 files assert that a layering violation is intentional and safe. At least three of them documented a permanently broken import as design intent. An inline annotation claiming safety is, to any assessor, a compensating-control claim — and compensating-control claims require evidence.

For each of the 19: either produce a test proving the suppressed condition is safe and add a reference to that test on the same line, or remove the suppression and fix the underlying inversion. There is no third option.

Record every verdict in `reports/remediation/D4_SUPPRESSIONS.md`.

**Exit gate**

```bash
# Every remaining suppression carries a test reference
grep -rn "inversion:ok" --include="*.py" . | grep -vE "inversion:ok \(see tests?/" | wc -l
# Gate: 0
test -f reports/remediation/D4_SUPPRESSIONS.md
```

---

### CR-D5 · Reconcile the capability manifest

**Depends on:** CR-A1
**Allowed paths:** KA registry/manifest files, `docs/`
**Sessions:** 1

The manifest marks roughly 211 of 213 canonical capabilities "production-enabled," while the live L1–L10 default path touches about 20 (KA-001–007, 010, 012, 013, 018, 022, 024, 027, 028, 030, 038, 061, 062, 1074, 1107). The rest are reachable through the selector, but "production-enabled" as a product claim means something stronger than "importable."

Introduce honest state values — for example `live-default`, `selector-reachable`, `implemented-untested` — and reclassify every capability against evidence. Generate the classification from the code rather than editing it by hand, so it cannot drift again.

**Exit gate**

```bash
python scripts/generate_ka_manifest.py --check   # exits nonzero if manifest disagrees with code
```

---

### CR-D6 · Retire or supersede the January standards assessment · `HUMAN-GATE`

**Allowed paths:** `docs/`

`UKG_Enterprise_Standards_Assessment.docx` scores the system at 86% enterprise-ready and marks "Confidence calibration (Brier)" as covered; no code computes it. As an internal design document that is a gap. As a claim shown to a buyer it is a representation.

Add a prominent header marking it as target-state design intent rather than an implementation status report, or supersede it with the blueprint. **Kevin decides which; the agent does not silently delete a document.**

**PHASE D EXIT GATE.** No default-on-failure returns in the score path; `core/simulation/` archived with zero dead imports; all suppressions evidenced or removed; manifest generated from code.

---

## PHASE E — Supply chain and manufacturer obligations

**Why this phase exists.** You ship code into environments your customers have accredited. Your build pipeline *is* the trust relationship. With the EU market out of scope there is no CRA conformity duty here — but SBOMs are requested at agency discretion under OMB M-26-05's risk-based regime, enterprise diligence expects them, and an unsigned Windows installer is a distribution blocker regardless of any regulation.

**Depends on:** Phase A complete
**Branch:** `remediation/phase-e`
**Sessions:** 4–6

### CR-E1 · SBOM generation per build — ✅ ALREADY SATISFIED (verified 2026-08-20)

> Implemented 2026-02-16 in `.github/workflows/release-installer-signing.yml`, step *"Generate release SBOMs and normalized content inventory"*. **Close this task.** Verify the emitted format is CycloneDX 1.6 and that the artifact is attached to releases; if both hold, no work remains.

**Allowed paths:** `.github/workflows/`, `scripts/build/`
**Sessions:** 1

CycloneDX 1.6 via `cdxgen` or `syft`, emitted on every build, attached to every release artifact, covering Python and any bundled JS/native dependencies. Store under `reports/sbom/` with the commit SHA in the filename.

**Exit gate**

```bash
test -f reports/sbom/*.cdx.json && \
python -c "import json,glob; d=json.load(open(glob.glob('reports/sbom/*.cdx.json')[0])); assert d['bomFormat']=='CycloneDX'; assert len(d['components'])>0; print(len(d['components']),'components')"
```

---

### CR-E2 · Security scanning gates in CI

**Allowed paths:** `.github/workflows/`, `.semgrep.yml`, `.gitleaks.toml`, `pyproject.toml`
**Sessions:** 1–2

Four required PR checks: SAST (Semgrep or CodeQL), dependency CVE scanning (`pip-audit`, Trivy, or Grype), secret scanning (`gitleaks`), and license compliance. Each needs a documented severity policy — what fails the build versus what files an issue. A scanner whose findings are all ignored is worse than no scanner, because it produces evidence of known-and-unaddressed defects.

**Exit gate**

```bash
grep -rq "semgrep\|codeql" .github/workflows/ && \
grep -rq "pip-audit\|trivy\|grype" .github/workflows/ && \
grep -rq "gitleaks" .github/workflows/ && \
test -f docs/VULNERABILITY_MANAGEMENT.md
```

---

### CR-E3 · Hermetic, reproducible build

**Allowed paths:** build config, `pyproject.toml`, lockfiles
**Sessions:** 1

Pinned toolchain, committed lockfile, no network access during build, deterministic outputs where achievable. Document any non-determinism that cannot be removed.

**Exit gate:** two consecutive clean builds produce byte-identical artifacts, or a documented explanation of each difference.

---

### CR-E4 · Signed installer and signed updates — ✅ ALREADY SATISFIED (verified 2026-08-20)

> Implemented 2026-02-16. `release-installer-signing.yml` performs unsigned build → secret validation → PFX decode → sign, and `code-signing-governance.yml` runs certificate rotation and revocation drills on `windows-latest`. **Close this task.** Owner signing authority (G-SIGN) is a separate, deferred decision. Remaining gap is rollback protection on the update path — fold into CR-E5.

**Allowed paths:** `scripts/build/`, `.github/workflows/`, docs
**Sessions:** 1–2

Authenticode signing on the Windows installer with an EV certificate. This is a practical distribution blocker before it is ever a compliance one — SmartScreen will flag an unsigned installer and most enterprise environments will refuse it outright.

Because there is no auto-update phone-home (a genuine privacy advantage), update *distribution* integrity matters more, not less: signed update packages, signature verification before applying, and rollback protection.

The agent implements the pipeline and stubs the signing step. **Certificate procurement is Kevin's; the agent stops at that boundary.**

**Exit gate:** signing step present and parameterized; verification logic tested against a self-signed test certificate; planned output docs/RELEASE_SIGNING.md written.

---

### CR-E5 · SLSA provenance attestations

**Depends on:** CR-E3, CR-E4
**Allowed paths:** `.github/workflows/`
**Sessions:** 1

Target SLSA Build Level 3. Emit in-toto provenance from the hermetic CI build; sign with Sigstore/cosign; attach to releases.

**Exit gate:** provenance attestation generated and verifiable with `cosign verify-attestation` against a test key.

---

### CR-E6 · FIPS-capable crypto abstraction · `HUMAN-GATE` on the module decision

**Allowed paths:** `backend/security/encryption_manager.py`, config
**Sessions:** 1–2

**The finding.** `EncryptionManager` implements real AES-256-GCM (`AESGCM.generate_key(bit_length=256)`, 12-byte nonce) with Fernet retained as the key-encryption-key wrapper — a correct envelope-encryption design. But AES-256-GCM is a FIPS-*approved algorithm*, and the default `cryptography` build is **not a FIPS-validated module**. For federal deployment the algorithm is not the question; module validation is. The same question applies to Windows DPAPI for the specific way it is used here.

The agent's job is not to pick a module — that is a procurement and platform decision. The agent's job is to make the choice pluggable: abstract the crypto provider behind an interface, add a FIPS-mode configuration flag, add a startup self-check that reports the active provider and its validation status, and document precisely what is and is not validated so nothing overclaims.

**Kevin decides** between FIPS-mode OpenSSL, Windows CNG in FIPS mode, or a validated HSM.

**Exit gate:** provider interface tested with at least two implementations; startup reports active provider; planned output docs/CRYPTOGRAPHY.md states validation status without overclaiming.

**PHASE E EXIT GATE.** SBOM, SAST, SCA, secret scanning, and license checks all gating PRs; hermetic build; signing pipeline present; crypto provider pluggable and honestly documented.

---

## PHASE F — Measure what the product claims

**Why this phase exists.** This is the only phase a *buyer* would notice. Three of the four load-bearing quality claims — calibrated confidence, sub-0.5% hallucination rate, 99.5% high-stakes accuracy — have no measurement apparatus, while the fourth (auditability) has 341,000 lines of evidence JSON behind it. The verification effort is real and pointed almost entirely inward.

One benchmark satisfies EU AI Act Art. 15 (declared accuracy metrics), ISO 42001 cl. 9.1 (performance evaluation), NIST AI RMF MEASURE 2.x, and SR 11-7 model validation — and it is the sales asset.

**Depends on:** Phase A complete; benefits from CR-D1
**Branch:** `remediation/phase-f`
**Sessions:** 5–8

### CR-F1 · Evaluation harness

**Allowed paths:** new `evals/`
**Sessions:** 2

Runs a fixed question set through the governed path, records answers with the governance score and full provenance, and writes results to `reports/evals/` with the commit SHA, model endpoint, and configuration. Deterministic where possible; seeds recorded where not.

**Exit gate:** harness runs end-to-end against a mock model and produces a structured result file.

---

### CR-F2 · Labeled evaluation set · `HUMAN-GATE` on content

**Allowed paths:** `evals/datasets/`
**Sessions:** 2

A held-out set with ground-truth labels. Domain content is Kevin's — the agent builds the schema, loaders, validation, and a documented provenance record for every item, then stops. Start small and real: 200 well-labeled items beat 2,000 synthetic ones, and synthetic ground truth generated by a model is not ground truth.

Recover the StrataMind benchmark referenced in the May plan (18 adversarial questions, 95.3/100) if its results still exist anywhere; the review could not find them in the tree.

**Exit gate:** schema validates; loader tested; provenance documented per item.

---

### CR-F3 · Calibration measurement

**Depends on:** CR-F1, CR-F2
**Allowed paths:** `evals/`
**Sessions:** 1–2

Compute expected calibration error and Brier score against the governance score; generate a reliability diagram. The current tree has zero hits for `expected_calibration_error`, `calibration_error`, `ECE`, and `brier`.

**Only after this exists** does re-implementing the spec'd formula (sigmoid, conflict penalty, entropy term) become a defensible change — because only then can you demonstrate it is an improvement rather than a different unvalidated number.

**Exit gate**

```bash
python -m evals.calibration --dataset evals/datasets/<set> --out reports/evals/calibration.json && \
python -c "import json; d=json.load(open('reports/evals/calibration.json')); assert 'ece' in d and 'brier' in d; print(d['ece'], d['brier'])"
```

---

### CR-F4 · Implement the hallucination-rate metric

**Depends on:** CR-F1, CR-F2
**Allowed paths:** `backend/truth_engine/truth_memory/metrics.py`, `evals/`
**Sessions:** 1–2

`hallucination_rate` currently exists as a key in a `METRIC_DEFINITIONS` dict — a slot to record a number into, with no code computing it. Implement the computation against the labeled set, with the measurement methodology documented explicitly enough that a third party could reproduce it.

This is LLM08 Misinformation, which OWASP moved up the 2026 list specifically because confidently-wrong output now drives automated business workflows — the pattern this product enables.

**Exit gate:** metric computed from the eval set; methodology documented; result written to `reports/evals/`.

---

### CR-F5 · Generate the system card from code

**Depends on:** CR-F3, CR-F4, CR-D5
**Allowed paths:** `docs/`, `scripts/`
**Sessions:** 1–2

The KA `limitations` pattern — capabilities returning explicit statements of what they did *not* establish — is the single best idea in this codebase and a code-level implementation of what ISO 42001 A.8.2 and NIST AI RMF MAP 3.4 ask for in prose. Most vendors write this in a PDF nobody reads; you compute it per invocation.

**This task also became the Colorado ADMTA compliance artifact.** Colorado repealed and replaced its AI Act on May 14, 2026 with the Automated Decision-Making Technology Act, effective **January 1, 2027**, which obliges *developers* of automated decision-making technology influencing consequential decisions in healthcare, lending, insurance, employment, education, housing, and government benefits to give deployers: documentation of intended use, known risks and **limitations**, categories of training data, instructions for meaningful human oversight, notice of material updates, and three-year record retention. The generated system card is five of those six. Build it to satisfy the statute and it satisfies ISO 42001 and NIST AI RMF at the same time — do not build three documents.

Aggregate it upward into a generated system card: intended use, out-of-scope uses, capability inventory with honest state values from CR-D5, measured accuracy and calibration from F3/F4, known limitations, and the measurement methodology.

**Generate it from the code, not by hand.** A hand-written system card drifts, and drift is what created this plan.

**Exit gate**

```bash
python scripts/generate_system_card.py --check   # nonzero if the card disagrees with code or eval results
```

**PHASE F EXIT GATE.** Measured ECE, Brier, and hallucination rate published in `reports/evals/`; system card generated from code and consistent with it.

---

## PHASE G — Ship the documentation artifacts

**Why last.** These describe what Phases A–F built. Written earlier, they document intent — which is exactly how the January assessment came to say things the code does not do.

**Depends on:** Phases B, C, D, E, F
**Branch:** `remediation/phase-g`
**Sessions:** 4–6

The deliverable is the **Product Security Package**: roughly 30 pages that answers most enterprise security questionnaires without a call, at a fraction of what a SOC 2 would cost — and SOC 2 does not apply to installed software anyway.

| ID | Artifact | Sourced from | Gate |
|---|---|---|---|
| CR-G1 | Coordinated Vulnerability Disclosure policy + `security.txt` (ISO 29147/30111) | — | Policy present; `security.txt` served at the well-known path; named contact. **Routine priority** — no longer CRA-driven, but federal procurement increasingly expects a published disclosure process. |
| CR-G2 | **US incident reporting runbook** *(replaces the withdrawn CRA runbook)* — DFARS 252.204-7012 72h reporting if handling CUI; CIRCIA 72h incident / 24h ransom-payment reporting once the final rule lands; customer contractual notification windows, which are usually tighter than statute | — | Runbook with named roles, destinations, and per-obligation clocks. Record the US-only market determination as the closing note on the withdrawn CRA scope. |
| CR-G3 | Data flow diagram + egress attestation | Phase B | Diagram matches `EGRESS_INVENTORY.md`; attestation cites the CI artifact from CR-B5 |
| CR-G4 | Planned output docs/DEPLOYMENT_HARDENING.md — CIS/STIG-aligned config, firewall rules, least-privilege service account, uninstall/decommission | Phase C, CR-C4 | Every setting referenced exists in the config schema (verify programmatically) |
| CR-G5 | NIST SSDF (SP 800-218 v1.1) mapping | Phases A, E | Every practice cites a file, workflow, or report path that exists. **Note:** OMB M-26-05 (Jan 23, 2026) rescinded the government-wide CISA Common Form attestation; agencies now validate on their own risk-based terms. Have the artifact ready on request rather than a form on file. |
| CR-G6 | NIST SP 800-218A (GenAI SSDF profile) mapping | Phases D, F | Same standard — every claim cites an artifact |
| CR-G7 | Customer Responsibility Matrix vs. NIST 800-53 Rev 5 | All | For each relevant control: product-provided / customer-provided / shared. **The single most valuable federal document you can write** — it makes an agency's ATO cheap. |
| CR-G8 | HIPAA Deployment Guide — Business Associate analysis, model-endpoint decision tree, PHI-safe diagnostics policy, §164.312 safeguard mapping | Phase B, CR-B4 | Guide present. `HUMAN-GATE`: **counsel reviews the BA determination before it goes to any customer.** |
| CR-G9 | PHI-safe support diagnostics | Phase B | Diagnostic bundles scrub content by default via the existing Presidio path; test proves no PHI-shaped content in a generated bundle |
| CR-G10 | Security update support period declaration | — | No longer a CRA duty, but buyers ask and federal ATOs need an end-of-support date. Stated in docs and surfaced in the installer. |
| CR-G11 | Incident response plan with AI-specific playbooks — prompt injection, model provider outage, confabulated-output harm, context leak | Phases B, D | Plan present with named roles and triggers |
| CR-G12 | Section 508 / WCAG 2.2 AA conformance report (ACR/VPAT) | — | Only if federal is in scope. Routinely forgotten until it blocks a deal at signature. |

**PHASE G EXIT GATE.** Every document's factual claims trace to an artifact produced by Phases A–F. **A claim with no artifact is deleted, not softened.**

---

## 2. Decisions only Kevin can make

The agent must halt at each of these. None should be guessed.

| # | Decision | Blocks | Why the agent cannot decide |
|---|---|---|---|
| 1 | Name for the renamed confidence score | CR-D1 | Product vocabulary and API compatibility |
| 2 | Disposition of the 91 uncommitted working-tree changes | CR-A0 | Only Kevin knows what is in flight |
| 3 | ~~Is the product placed on the EU market?~~ | ~~CR-G1, CR-G2~~ | **RESOLVED 2026-08-18: no. US market only.** CRA, EU AI Act, GDPR, NIS2, and DORA are all out of scope. CR-G2 replaced with a US incident reporting runbook. |
| 4 | FIPS crypto module choice (OpenSSL FIPS / Windows CNG / HSM) | CR-E6 | Procurement and platform-support decision |
| 5 | EV code-signing certificate procurement | CR-E4 | Purchase and identity verification |
| 6 | Labeled evaluation set content and ground truth | CR-F2 | Domain expertise; synthetic ground truth is not ground truth |
| 7 | Retire vs. re-header the January assessment | CR-D6 | Do not silently delete a document |
| 8 | Retiring any test | CR-A3, CR-D3 | A deleted test is a removed control |
| 9 | Does this supersede Phase 19 or run parallel? | plan-wide | Release strategy |

---

## 3. Anti-goals for the whole program

Things that will look like progress and are not:

- **A fourteenth Phase 19 checkpoint.** Integration correctness is established. More internal evidence does not answer the open question.
- **More evidence JSON.** There are already 340,934 lines against 160,000 lines of source. Adding to that ratio is not remediation.
- **Certification prep before Phase F.** ISO 42001 and ISO 27001 are worth pursuing — after there is something true to certify. Starting the paperwork first produces a certificate describing a system that does not exist.
- **Re-implementing the sigmoid confidence formula early.** Without calibration measurement it is one unvalidated number swapped for another.
- **Rewriting the January assessment to be more accurate.** Supersede it. Do not maintain two assessments.
- **Broadening any task's scope because the agent noticed something adjacent.** File it as a finding; do not fix it in-flight.

---

## 4. Program exit criteria — what "done" means

1. Full test suite green on Windows CI with zero collection errors; collected count ≥ 3,126.
2. A dated CI egress attestation showing exactly one contacted host class, reproducible on demand.
3. Air-gap mode proven end-to-end against a local model.
4. Every local-API security test executing and passing on the shipping platform.
5. No default-on-failure return anywhere in the governance score path.
6. `core/simulation/` archived; zero references to the nonexistent `backend.knowledge_algorithm`.
7. Every suppression comment backed by a test or removed.
8. SBOM, SAST, SCA, secret scanning, and license checks gating every PR.
9. Signed installer and signed update path.
10. Published ECE, Brier, and hallucination rate against a real labeled set.
11. System card generated from code and consistent with it, and sufficient as the Colorado ADMTA developer-documentation package (effective January 1, 2027).
12. Product Security Package complete, with every claim tracing to an artifact.

When those twelve hold, `release_blocked` comes off — and, more usefully, the answer the system gives about itself is finally as strong as the answer it promises about everything else.

---

*Companion file: `ukg_remediation_tasks.json` — the same tasks as structured data with dependencies, gates, and allowed paths, suitable for driving an agent runner or importing as issues.*
