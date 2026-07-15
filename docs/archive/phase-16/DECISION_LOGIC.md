# Decision Logic Reference — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v3.2.0 |
| Last updated | 2026-07-14 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Software engineers, architects, QA, security reviewers, technical evaluators |
| Review cadence | Every 60 days |

## Purpose

Capture the significant decision points in DataLogicEngine: what is evaluated, what outcomes are possible, and where the decision is implemented.

This version reflects the Phase 6 evidence-quality and convergence contract on
the Phase 5 `governed.v1` causal request path. Older
conceptual references and private compatibility helpers are not independent
answer-producing architectures.

## Related documents

1. `docs/WORKFLOW.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ARCHITECTURE_MAP.md`
4. `docs/DATA_FLOW_DIAGRAMS.md`
5. `docs/SECURITY.md`
6. `docs/API.md`
7. `docs/DATABASE_SCHEMA.md`
8. `docs/PRODUCTION_READINESS.md`

---

## Decision index

| ID | Decision | Primary implementation |
|---|---|---|
| DL-01 | Runtime mode selection | `frontend/lib/runtime/policy.ts`, `backend/storage/connection_manager.py` |
| DL-02 | Authentication path selection | `frontend/contexts/AuthContext.tsx`, `backend/security/desktop_local_auth.py`, auth routes |
| DL-03 | API route/auth error behavior | `app.py`, `backend/auth/api_decorators.py`, route modules |
| DL-04 | Governed admission and DMRF injection-defense decision | `backend/governed_execution/orchestrator.py`, `backend/dmrf/injection_defense.py` |
| DL-05 | TruthGate allow/block/warn decision | `backend/truth_engine/truth_gate/gateway.py` |
| DL-06 | Tier classification | `backend/dmrf/tier_classifier.py` |
| DL-07 | 17-axis routing and FROST mode | `backend/dmrf/router.py`, `core/axes/` |
| DL-08 | Deterministic DSQP persona construction | `backend/governed_execution/orchestrator.py`, `backend/dsqp/` |
| DL-09 | TruthCore/KA workflow decision | `backend/governed_execution/orchestrator.py` |
| DL-10 | Evidence and validation decision | `backend/governed_execution/retrieval.py`, `backend/governed_execution/validation.py` |
| DL-11 | Provider/model execution decision | `backend/governed_execution/prompt.py`, `backend/llm_gateway/` |
| DL-12 | MCP scope/tool decision | `backend/mcp_server/`, MCP routes/services |
| DL-13 | Storage mode decision | `backend/storage/connection_manager.py` |
| DL-14 | Export integrity decision | `backend/security/export_integrity.py` |
| DL-15 | Release readiness decision | `docs/RELEASE_CHECKLIST.md`, `scripts/verify_release_governance.py` |

---

## DL-01: Runtime mode selection

Runtime mode determines trust boundaries, authentication behavior, storage assumptions, and deployment checks.

```text
INPUT: runtime environment + config + Electron/loopback context

IF local desktop/Electron loopback context is detected
  -> local-first / desktop mode
  -> desktop local-auth path may apply
  -> app-owned local stores are valid

ELSE IF Windows VM/internal deployment is configured
  -> VM/local-stack mode
  -> app-owned stores remain internal to the VM

ELSE
  -> web/cloud mode
  -> web/session auth required
  -> HTTPS, trusted hosts, CORS, CSRF, secure cookies required
```

Key rule: desktop local trust must not be promoted to public web/cloud trust.

---

## DL-02: Authentication path selection

```text
INPUT: request origin + runtime mode + session state + desktop headers/signature

IF canonical API request is already authenticated by session/token
  -> allow route permission evaluation

ELSE IF desktop/local mode AND loopback/Electron criteria are satisfied
  -> run desktop local-auth challenge/verification
  -> allow only if nonce/HMAC/timestamp checks pass

ELSE IF web/cloud route
  -> require web login/session auth

ELSE
  -> reject with JSON-native 401/403 for API routes
```

Desktop local-auth checks include:

1. install secret;
2. nonce challenge;
3. HMAC signature;
4. timestamp skew;
5. constant-time comparison;
6. DPAPI helper where available.

---

## DL-03: API route/auth error behavior

Canonical application APIs use `/api/v1/*`.

Decision rules:

```text
IF route is canonical /api/v1/*
  -> return JSON-native responses
  -> auth failure returns 401/403 JSON
  -> no browser login redirect

IF route is browser/page route
  -> browser redirect behavior may apply

IF route is legacy /api/* compatibility alias
  -> preserve compatibility where supported
  -> emit deprecation/successor metadata where implemented
```

New integrations should target `/api/v1/*`.

---

## DL-04: DMRF injection-defense decision

Primary implementation: `backend/dmrf/injection_defense.py`.

Decision categories include:

1. no injection detected;
2. prompt injection;
3. logical trap;
4. obfuscated payload;
5. persona hijack;
6. resource exhaustion.

```text
INPUT: user prompt + context

IF mode == simulation
  -> stop the ordinary answer path after admission
  -> return SIMULATION_DURABLE_JOB_REQUIRED
  -> direct the caller to /api/v1/simulations

ELSE IF category == none and severity below threshold
  -> continue to TruthGate

IF suspicious but recoverable
  -> continue with warnings/trace metadata where implemented

IF blocked category/severity is reached
  -> fail closed
  -> return structured block response
  -> persist audit/trace signal
```

Security rule: do not silently bypass injection defense on failure.

---

## DL-05: TruthGate decision

Primary implementation: `backend/truth_engine/truth_gate/gateway.py`.

TruthGate evaluates gate context such as:

1. security;
2. budget;
3. compliance;
4. priority;
5. trust;
6. PII markers;
7. blocked patterns.

Possible outcomes:

| Outcome | Meaning |
|---|---|
| allow | request can proceed. |
| warn | request can proceed with caveat/trace metadata. |
| block | request must not continue. |
| escalate/review | human or operator review is recommended/required where implemented. |

---

## DL-06: Tier classification

Primary implementation: `backend/dmrf/tier_classifier.py`.

Current tiers:

1. trivial;
2. moderate;
3. high_stakes;
4. extreme;
5. autonomous.

```text
INPUT: prompt + risk/complexity/context signals

IF simple deterministic/low-risk
  -> trivial

ELSE IF normal analysis/context required
  -> moderate

ELSE IF regulated/high-impact/legal/security/compliance context
  -> high_stakes

ELSE IF complex simulation/cross-domain/deep reasoning required
  -> extreme

ELSE IF autonomous planning or governed multi-step execution required
  -> autonomous
```

Desktop/offline mode may cap or restrict higher-risk autonomous behaviors.

---

## DL-07: 17-axis routing and FROST mode

Primary implementation: `backend/dmrf/router.py`, `core/axes/`.

The router maps request context to coordinate/routing metadata.

Key modern emphasis:

1. axes 1-13 provide domain/location/time/role context;
2. Axis 15 maps risk/threat context;
3. Axis 16 maps ethics/trust/criticality context;
4. Axis 17 maps FROST depth and TruthCore mode.

```text
INPUT: request + tier + context

Resolve active axes
  -> produce coordinate vector
  -> determine FROST depth / TruthCore mode
  -> attach routing metadata to DMRF trace
```

---

## DL-08: DSQP persona construction

Primary implementation: `backend/governed_execution/orchestrator.py` with the
DSQP modules as deterministic inputs.

DSQP constructs structured personas from axes 8-11.

Persona families:

1. Knowledge Expert;
2. Sector Expert;
3. Regulatory Expert;
4. Compliance Expert.

Each traced persona may include:

1. job role;
2. education;
3. certifications;
4. skills;
5. training;
6. career path;
7. related jobs.

```text
INPUT: 17-axis context + role axes

Build deterministic structured persona context from axes 8-11
  -> include selected contribution in the provider prompt
  -> persist the exact contribution in trace

IF a contribution is not used
  -> do not claim it influenced the answer
```

Cloud-generated persona construction is disabled in the canonical path. A later
explicitly consented feature would need to count its provider calls and prove
that its output causally affected the result.

---

## DL-09: TruthCore workflow decision

Primary implementation: `backend/governed_execution/orchestrator.py`. The public
`TruthCoreEngine.process()` method is a compatibility adapter into the canonical
gateway; it is not a second public orchestrator.

TruthCore determines workflow depth and execution plan.

```text
INPUT: mode + tier + TruthGate result + 17-axis route + DSQP context

IF TruthGate blocks
  -> no TruthCore, KA, or provider execution

IF standard
  -> select bounded workflow and execute required KA-113 preflight

IF enhanced
  -> select bounded deeper workflow and execute KA-113 plus KA-001 preflight

IF local_review
  -> perform local review without claiming a provider answer

IF simulation
  -> require the separate dle-simulation.v1 durable job contract
```

Only executed KAs are persisted. A KA shown in trace must have its real input,
output, status, and duration. Phase 6 validates whether each KA result is
category-appropriate and evidentially sufficient.

---

## DL-10: Evidence and convergence decision

Primary implementations:

- `backend/governed_execution/retrieval.py`
- `backend/governed_execution/validation.py`

```text
INPUT: bounded source-identified evidence + provider output + claims/citations

Reject suspicious or malformed retrieval chunks
  -> assign stable per-run source labels to accepted chunks
  -> include accepted evidence in the provider request
  -> validate output/claim/citation/policy shape

bind each accepted evidence item to the trace ID
  -> derive stable evidence ID from trace + source + content hash
  -> measure explicit provenance completeness, source quality, and freshness
  -> leave any unavailable component null/not_measured

extract stable factual claims and citation offsets
  -> resolve citation to persisted evidence
  -> classify relationship as supports, contradicts, or insufficient

calculate dle-confidence.v1 evidence-support coverage
  -> claim support 0.35
  -> claim consistency 0.10
  -> explicit source quality 0.20
  -> provenance completeness 0.15
  -> freshness 0.10
  -> validator pass rate 0.10

IF any named component is unavailable
  -> return confidence = null and status = not_measured

IF evidence-required claims are contradicted or insufficient
  -> enhanced mode may refine once
  -> then abstain at the bound

IF a policy validator fails
  -> block

IF validation fails
  -> return typed validation_failure
  -> do not record completed persistence stages that never executed
```

The numeric value is evidence-support coverage, not the probability that an
answer is correct. Text length, routing/stage completion, hashes, and debate
turns are not confidence inputs. OpenAI/Google calibration and blinded human
acceptance remain rebuilt-installed release gates.

---

## DL-11: Provider/model execution decision

Primary implementation: `backend/llm_gateway/`.

```text
INPUT: one approved prompt containing policy constraints, evidence source IDs,
       DSQP contributions, KA results, and user query

IF deterministic/local processing is sufficient
  -> do not call provider

ELSE IF provider credentials/model config exists and budget remains
  -> call configured provider/model within the request call bound
  -> record latency/usage/error metadata

ELSE
  -> return structured provider-unavailable error
```

Rules:

1. Do not fabricate success when provider calls fail.
2. Do not log raw provider secrets.
3. Provider calls may transmit selected context outside the local machine.
4. Provider tests should return specific failure reasons where available.
5. A policy block or simulation boundary is not a provider/network failure.
6. `run_ukg_pipeline=false` is deprecated and never bypasses governance.
7. Recursive entry into governed execution is refused.

---

## DL-12: MCP scope/tool decision

Primary implementation: `backend/mcp_server/` and MCP route/service modules.

```text
INPUT: requested tool + user/tenant context + connector config + scopes

IF connector disabled or unavailable
  -> deny/return unavailable

IF required scope missing
  -> deny and audit

IF request contract invalid
  -> reject before outbound call

IF allowed
  -> execute tool call
  -> validate response contract
  -> record trace/metrics
```

---

## DL-13: Storage mode decision

Primary implementation: `backend/storage/connection_manager.py`.

```text
INPUT: deployment mode + local services + config

IF local/desktop mode
  -> prefer app-owned local stores / SQLite fallback where configured

IF Windows VM mode
  -> use internal VM app-owned stack

IF cloud mode
  -> use explicitly configured production stores
  -> do not rely on desktop storage assumptions
```

Production rule: `AUTO_CREATE_SCHEMA=true` is not valid production behavior.

---

## DL-14: Export integrity decision

Primary implementation: `backend/security/export_integrity.py`.

```text
INPUT: export request + sections + signing/encryption config

Always:
  -> compute section hashes
  -> compute bundle hash
  -> generate manifest

IF HMAC enabled
  -> sign manifest/payload metadata

IF encryption enabled
  -> encrypt export payload

Return:
  -> export bundle + manifest + integrity metadata
```

Exported bundles may leave the application boundary and must be handled as sensitive artifacts.

---

## DL-15: Release readiness decision

Primary references:

- `docs/RELEASE_CHECKLIST.md`
- `docs/PRODUCTION_READINESS.md`
- `scripts/verify_release_governance.py`

```text
INPUT: release type + CI results + validation artifacts + caveats

IF local engineering/demo release
  -> require local validation and documented caveats

IF desktop release candidate
  -> require backend rebuild, Electron/NSIS packaging, installer integrity, portable smoke, installer-mode smoke where scoped, and NSIS governance

IF signed Windows production release
  -> require trusted signing and signature verification evidence

IF web/cloud production release
  -> require HTTPS/TLS, secure cookies, provider staging validation, health/readiness/metrics, rollback evidence

IF required evidence missing
  -> block or approve only with explicit caveat/waiver
```

---

## Cross-cutting decision rules

1. Fail closed for security gate failures.
2. Prefer structured JSON errors for canonical API routes.
3. Prefer traceable uncertainty over false confidence.
4. Do not claim compliance beyond evidence.
5. Do not silently hide provider/tool failures.
6. Do not treat local-first as air-gapped.
7. Do not treat desktop local-auth as cloud trust.
8. Persist decision metadata where trace/audit is expected.

## Change notes for v3.0.0

1. Aligned admission, DSQP, TruthCore/KA, evidence/validation, and provider
   decisions with the implemented `governed.v1` orchestrator.
2. Removed plan-only convergence/default-persona implications and documented
   null confidence plus the Phase 6 validity boundary.

## Change notes for v2.7.0

1. Expanded the desktop release readiness decision to include backend rebuild, installer integrity, portable smoke, installer-mode smoke, and NSIS governance.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older Active Defense, QuadPersona, legacy provider-routing, and earlier tier details with current DMRF/Truth Engine/DSQP decision model.
3. Added decision index and 15 current decision areas.
4. Added cross-cutting decision rules aligned with security, privacy, release, and API governance docs.
