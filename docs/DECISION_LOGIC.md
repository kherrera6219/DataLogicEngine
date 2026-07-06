# Decision Logic Reference — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Software engineers, architects, QA, security reviewers, technical evaluators |
| Review cadence | Every 60 days |

## Purpose

Capture the significant decision points in DataLogicEngine: what is evaluated, what outcomes are possible, and where the decision is implemented.

This version reflects the current DMRF + Truth Engine + 17-axis + DSQP + local-first architecture. Older conceptual references such as generic QuadPersona or Supervisor-LLM Active Defense are not treated as current source-of-truth unless implemented by the current modules below.

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
| DL-04 | DMRF injection-defense decision | `backend/dmrf/injection_defense.py` |
| DL-05 | TruthGate allow/block/warn decision | `backend/truth_engine/truth_gate/gateway.py` |
| DL-06 | Tier classification | `backend/dmrf/tier_classifier.py` |
| DL-07 | 17-axis routing and FROST mode | `backend/dmrf/router.py`, `core/axes/` |
| DL-08 | DSQP persona construction | `backend/dsqp/dsqp_chain.py` |
| DL-09 | TruthCore workflow decision | `backend/truth_engine/truth_core/engine.py` |
| DL-10 | Evidence/convergence decision | `backend/dmrf/evidence_model.py`, `backend/dmrf/convergence_policy.py` |
| DL-11 | Provider/model execution decision | `backend/llm_gateway/` |
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

IF category == none and severity below threshold
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

Primary implementation: `backend/dsqp/dsqp_chain.py`.

DSQP constructs structured personas from axes 8-11.

Persona families:

1. Knowledge Expert;
2. Sector Expert;
3. Regulatory Expert;
4. Compliance Expert.

Each persona may include:

1. job role;
2. education;
3. certifications;
4. skills;
5. training;
6. career path;
7. related jobs.

```text
INPUT: 17-axis context + role axes

IF persona context is needed
  -> build deterministic structured persona set
  -> attach to workflow/trace

ELSE
  -> skip persona construction or use default lightweight context
```

---

## DL-09: TruthCore workflow decision

Primary implementation: `backend/truth_engine/truth_core/engine.py`.

TruthCore determines workflow depth and execution plan.

```text
INPUT: tier + TruthGate result + 17-axis route + DSQP personas

IF trivial
  -> shallow workflow

IF moderate
  -> normal governed workflow

IF high_stakes/extreme/autonomous
  -> deeper workflow with additional evidence/convergence/review controls

IF blocked or insufficient evidence
  -> safe fallback or refusal/block path
```

TruthCore should not treat provider output as final without policy/evidence handling when a governed workflow requires review.

---

## DL-10: Evidence and convergence decision

Primary implementations:

- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`

```text
INPUT: evidence items + claims + tier + freshness/confidence signals

IF evidence is fresh/sufficient and convergence threshold is met
  -> finalize

IF evidence is stale/insufficient but recoverable
  -> refine/retry/deepen workflow

IF evidence cannot support answer
  -> safe fallback / uncertainty / human review recommendation
```

---

## DL-11: Provider/model execution decision

Primary implementation: `backend/llm_gateway/`.

```text
INPUT: workflow plan + configured providers + model settings + credentials

IF deterministic/local processing is sufficient
  -> do not call provider

ELSE IF provider credentials/model config exists
  -> call configured provider/model
  -> record latency/usage/error metadata

ELSE
  -> return structured provider-unavailable error
```

Rules:

1. Do not fabricate success when provider calls fail.
2. Do not log raw provider secrets.
3. Provider calls may transmit selected context outside the local machine.
4. Provider tests should return specific failure reasons where available.

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

## Change notes for v2.7.0

1. Expanded the desktop release readiness decision to include backend rebuild, installer integrity, portable smoke, installer-mode smoke, and NSIS governance.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older Active Defense, QuadPersona, legacy provider-routing, and earlier tier details with current DMRF/Truth Engine/DSQP decision model.
3. Added decision index and 15 current decision areas.
4. Added cross-cutting decision rules aligned with security, privacy, release, and API governance docs.
