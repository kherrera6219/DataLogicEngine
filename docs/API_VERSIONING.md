# API Versioning Strategy

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Platform Architecture + API Governance |
| Review cadence | Every 60 days |

## Purpose

Define how DataLogicEngine versions application APIs, manages compatibility aliases, communicates deprecation, and validates route behavior.

This version aligns with the current API architecture: canonical `/api/v1/*` application routes, supported operational namespaces, legacy compatibility aliases, JSON-native auth failures, route contract tests, and release-governed deprecation behavior.

## Related documents

1. `docs/API.md`
2. `docs/ARCHITECTURE.md`
3. `docs/TESTING.md`
4. `docs/RELEASE_CHECKLIST.md`
5. `docs/PRODUCTION_READINESS.md`
6. `tests/contract/`

---

## Current API version

The current primary application API version is:

```text
v1
```

Canonical application endpoints use:

```text
/api/v1/*
```

Examples:

1. `/api/v1/auth/check`
2. `/api/v1/simulations`
3. `/api/v1/truth/health`
4. `/api/v1/trace/runs`
5. `/api/v1/privacy/*`
6. `/api/v1/storage/*`

---

## Route families

### Canonical application routes

New application integrations should use `/api/v1/*`.

Rules:

1. Auth failures must return JSON-native `401` or `403` responses.
2. Malformed requests should return deterministic validation errors.
3. Route behavior should be covered by contract or integration tests.
4. Public API changes must update `docs/API.md` and contract tests.

### Supported operational namespaces

Some operational or documentation namespaces may remain unversioned when they are not primary application integration contracts.

Examples include:

1. `/health`
2. `/live`
3. `/ready`
4. `/metrics`
5. `/api/docs`

Operational namespaces should be documented clearly and tested for expected behavior.

### Compatibility aliases

Compatibility aliases exist to support older clients and migration coverage. They are not the preferred integration path.

Representative compatibility aliases:

| Compatibility alias | Successor route family |
|---|---|
| `/api/compliance/*` | `/api/v1/compliance/*` |
| `/api/ka/*` | `/api/v1/ka/*` |
| `/api/mcp/*` | `/api/v1/mcp/*` |
| `/api/persona/*` | `/api/v1/persona/*` |
| `/api/pillar/*` | `/api/v1/pillar/*` |
| `/api/simulations/*` | `/api/v1/simulations/*` |
| `/api/truth/*` | `/api/v1/truth/*` |
| `/api/ukg/*` | `/api/v1/*` successor where implemented |

Compatibility aliases should emit deprecation/successor metadata where implemented.

---

## Versioning rules

### Major version bump required

A new major version such as `/api/v2/*` is required for:

1. breaking request schema changes;
2. breaking response schema changes;
3. endpoint removal;
4. incompatible authentication behavior changes;
5. incompatible status-code semantics;
6. removal of fields that clients may depend on;
7. behavioral changes that existing clients cannot safely ignore.

### No major version bump required

A major version bump is usually not required for:

1. adding optional fields;
2. adding new endpoints;
3. adding new optional query parameters;
4. bug fixes that restore documented behavior;
5. performance improvements;
6. adding deprecation headers without removing behavior;
7. adding stricter tests for already documented behavior.

---

## Deprecation policy

Before removing or breaking an existing route:

1. Document deprecation in `docs/API.md` and changelog/release notes.
2. Add deprecation headers where practical.
3. Add a `Sunset` header when a removal date is known.
4. Add `Link: <successor>; rel="successor-version"` where a successor exists.
5. Maintain compatibility for at least one release cycle unless a security issue requires faster removal.
6. Add or update tests proving both canonical and deprecated behaviors.
7. Record removal in the release checklist.

Example headers:

```http
Deprecation: true
Sunset: Wed, 30 Sep 2026 00:00:00 GMT
Link: </api/v1/simulations>; rel="successor-version"
```

---

## Version header

Clients may send a version hint:

```http
Accept: application/json
X-API-Version: 2026-05-30
```

The route path remains authoritative. `X-API-Version` is a behavior hint and trace/debug signal unless a route explicitly documents header-based behavior.

---

## Contract testing requirements

Route/version changes require test updates.

Relevant test areas:

1. `tests/contract/`
2. `tests/integration/`
3. `tests/integration_routes/`
4. `tests/security/`
5. `tests/parity/`

Required checks for canonical `/api/v1/*` changes:

1. unauthenticated behavior;
2. malformed request behavior;
3. happy-path status and response shape;
4. role/admin behavior where applicable;
5. deprecation headers for compatibility aliases;
6. no browser-style redirects for canonical API auth failures.

---

## Release governance

### Phase 1 security-baseline rule

The 2026 production-completion baseline intentionally removes unsafe behavior
without preserving it as compatibility: anonymous mutations, external-key
owner/admin access, public diagnostic detail, caller-owned MCP identity/scope,
raw exception strings, and renderer-supplied filesystem paths are not supported
contracts. Clients must use the versioned gateway and documented principal
tier. These trust-boundary corrections require contract tests and release notes
but do not justify a compatibility alias for the insecure behavior.

The generated route/surface manifest is versioned evidence. Any new route,
GraphQL operation, IPC channel, MCP method, file capability, or listener must be
classified before merge.

## Change notes for v2.8.0

1. Defined Phase 1 security corrections as non-compatible unsafe behavior rather than supported legacy contracts.
2. Added non-HTTP surface classification to API governance.

API versioning changes must be reflected in:

1. `docs/API.md`;
2. this document;
3. `docs/RELEASE_CHECKLIST.md` if release-impacting;
4. contract/integration/security tests;
5. changelog/release notes;
6. client migration guidance when applicable.

## Change notes for v2.7.0

1. Reviewed canonical `/api/v1/*` versioning policy during the production top-level documentation pass; policy remains active and unchanged.
2. Updated metadata so this source-of-truth policy is no longer dated to the May documentation baseline.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Clarified canonical `/api/v1/*` application route policy.
3. Added operational namespace and compatibility alias sections.
4. Added JSON-native API auth behavior guidance.
5. Added contract testing and release governance requirements.
